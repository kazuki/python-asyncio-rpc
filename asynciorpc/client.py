from asynciorpc import asyncio
from asynciorpc import ensure_future
from asynciorpc.rpc import ClientRpc
from asynciorpc.rpc import JsonRpc
from asynciorpc.rpc import MsgPackRpc


class Client(object):
    def __init__(self, addr, port, rpc_type='json'):
        self._addr = addr
        self._port = port
        self._loop = asyncio.get_event_loop()
        self._protocol = None
        self._conn_timeout = 60
        self._waiting = {}
        rpc_cls = JsonRpc
        if rpc_type == 'msgpack':
            rpc_cls = MsgPackRpc
        self._create_rpc = lambda: ClientRpc(
            rpc_cls(), self._handler, self._error, self._connection_lost)
        self._lock = asyncio.Lock()

    def close(self):
        if self._protocol and self._protocol.transport:
            self._protocol.transport.close()
            self._protocol = None

    def _handler(self, req_id, response):
        self._waiting[req_id].set_result(response)
        del self._waiting[req_id]

    def _error(self, req_id, reason):
        self._waiting[req_id].set_exception(Exception(reason))
        del self._waiting[req_id]

    def _connection_lost(self, exc):
        self._protocol = None
        for v in self._waiting.values():
            v.set_exception(None)

    def call(self, name, *args, **kwargs):
        return self._loop.run_until_complete(
            self.call_async(name, *args, **kwargs))

    def call_async(self, name, *args, **kwargs):
        if self._protocol is None:
            return ensure_future(self._connect(False, name, *args, **kwargs))
        else:
            fut = asyncio.Future(loop=self._loop)
            req_id = self._protocol.request(False, name, *args, **kwargs)
            self._waiting[req_id] = fut
            return fut

    @asyncio.coroutine
    def _connect(self, notify, name, *args, **kwargs):
        if self._protocol is None:
            with (yield from self._lock):
                if self._protocol is None:
                    fut = self._loop.create_connection(self._create_rpc,
                                                       self._addr, self._port)
                    _, self._protocol = yield from asyncio.wait_for(
                        fut, self._conn_timeout)
        req_id = self._protocol.request(notify, name, *args, **kwargs)
        fut = asyncio.Future(loop=self._loop)
        self._waiting[req_id] = fut
        return (yield from fut)
