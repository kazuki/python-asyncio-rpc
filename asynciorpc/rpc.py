from asynciorpc import asyncio
from asynciorpc import ensure_future


REQUEST_MESSAGE = 0
RESPONSE_MESSAGE = 1
ERROR_MESSAGE = 2


class RpcBase(asyncio.Protocol, asyncio.DatagramProtocol):
    def __init__(self):
        self.rpc = None
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        if self.rpc is None:
            if data[0:1] == b'{':
                self.rpc = JsonRpc()
            elif data[0] == 0x93 or data[0] == 0x94:
                self.rpc = MsgPackRpc()
            else:
                self.transport.close()
                return
        for msg in self.rpc.data_received(data):
            ensure_future(self.handle_message(msg))

    @asyncio.coroutine
    def handle_message(self, msg):
        pass


class ServerRpc(RpcBase):
    def __init__(self, handler):
        super(ServerRpc, self).__init__()
        self.handler = handler

    def connection_lost(self, exc):
        pass

    @asyncio.coroutine
    def handle_message(self, msg):
        if msg[0] != REQUEST_MESSAGE:
            print('ServerRpc::handle_message bug')
            return
        _, req_id, name, args, kwargs = msg
        ret = self.handler(name, *args, **kwargs)
        if req_id is not None:
            response = self.rpc.response(req_id, ret)
            self.transport.write(response)


class ClientRpc(RpcBase):
    def __init__(self, rpc, handler, error_handler, lost_callback):
        super(ClientRpc, self).__init__()
        self.rpc = rpc
        self.handler = handler
        self.lost_callback = lost_callback

    def connection_lost(self, exc):
        self.lost_callback(exc)

    def request(self, notify, name, *args, **kwargs):
        req_id, msg = self.rpc.request(notify, name, *args, **kwargs)
        self.transport.write(msg)
        return req_id

    @asyncio.coroutine
    def handle_message(self, msg):
        if msg[0] == REQUEST_MESSAGE:
            print('ClientRpc::handle_message bug')
            return
        _, req_id, body = msg
        if msg[0] == RESPONSE_MESSAGE:
            self.handler(req_id, body)
        else:
            self.error_handler(req_id, body)


class JsonRpc(object):
    def __init__(self):
        import json
        self._data = u''
        self._id = 0
        self._decoder = json.JSONDecoder()
        self._encoder = json.JSONEncoder(ensure_ascii=False,
                                         separators=(',', ':'))

    def request(self, notify, name, *args, **kwargs):
        if len(args) > 0 and len(kwargs) > 0:
            raise ValueError
        req = {
            'jsonrpc': '2.0',
            'method': name,
            'params': args if len(args) > 0 else kwargs
        }
        if len(args) == 0 and len(kwargs):
            del req['params']
        if not notify:
            req['id'] = self._id
            self._id += 1
            if self._id > 0xffffffff:
                self._id = 0
        return req['id'], self._encoder.encode(req).encode('utf-8')

    def response(self, req_id, response):
        req = {
            'jsonrpc': '2.0',
            'id': req_id,
            'result': response
        }
        return self._encoder.encode(req).encode('utf-8')

    def data_received(self, data):
        messages = []
        self._data += data.decode('utf-8')
        while len(self._data) > 0:
            try:
                obj, pos = self._decoder.raw_decode(self._data)
            except Exception:
                break

            self._data = self._data[pos:]
            if obj.get('jsonrpc', '') != '2.0':
                print('not jsonrpc 2.0')
                continue

            req_id = obj.get('id', None)
            if 'method' in obj:
                name = obj.get('method', None)
                if not name:
                    print('method name is empty')
                    continue
                params = obj.get('params', None)
                args = params if isinstance(params, list) else []
                kwargs = params if isinstance(params, dict) else {}
                messages.append((REQUEST_MESSAGE,
                                 req_id,
                                 name,
                                 args,
                                 kwargs))
            elif 'result' in obj:
                if req_id is None:
                    print('req-id is None')
                    continue
                result = obj.get('result', None)
                messages.append((RESPONSE_MESSAGE,
                                 req_id,
                                 result))
            elif 'error' in obj:
                if req_id is None:
                    print('req-id is None')
                    continue
                if 'message' in obj['error']:
                    desc = obj['error']['message']
                elif 'code' in obj['error']:
                    desc = str(obj['error']['code'])
                else:
                    desc = None
                messages.append((ERROR_MESSAGE,
                                 req_id,
                                 desc))
            else:
                print('unknown format')
                continue
        return messages


class MsgPackRpc(object):
    def __init__(self):
        import msgpack
        self._id = 0
        self._packer = msgpack.Packer(use_bin_type=True)
        self._unpacker = msgpack.Unpacker(encoding='utf-8')

    def request(self, notify, name, *args, **kwargs):
        if len(kwargs) > 0:
            raise ValueError
        if notify:
            req = (2, name, args)
            req_id = None
        else:
            req_id = self._id
            req = (0, req_id, name, args)
            self._id += 1
            if self._id > 0xffffffff:
                self._id = 0
        return req_id, self._packer.pack(req)

    def response(self, req_id, response):
        return self._packer.pack((1, req_id, None, response))

    def data_received(self, data):
        self._unpacker.feed(data)
        messages = []
        for obj in self._unpacker:
            if obj[0] == 0:
                messages.append((REQUEST_MESSAGE,
                                 obj[1],
                                 obj[2],
                                 obj[3],
                                 {}))
            elif obj[0] == 1:
                if obj[2] is None:
                    messages.append((RESPONSE_MESSAGE,
                                     obj[1],
                                     obj[3]))
                else:
                    messages.append((ERROR_MESSAGE,
                                     obj[1],
                                     obj[2]))
            elif obj[0] == 2:
                messages.append((REQUEST_MESSAGE,
                                 None,
                                 obj[1],
                                 obj[2],
                                 {}))
        return messages
