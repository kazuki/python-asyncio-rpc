from asynciorpc import asyncio
from asynciorpc.rpc import ServerRpc


class Server(object):
    def __init__(self, addr=None, port=None, sock=None):
        self._loop = asyncio.get_event_loop()
        if sock is None:
            pf = lambda: ServerRpc(self._handler)
            self._server_mode = True
            self._protocol = self._loop.run_until_complete(
                self._loop.create_server(pf, addr, port))
        else:
            pf = lambda: ServerRpc(self._handler, self._connection_lost)
            self._server_mode = False
            _, self._protocol = self._loop.run_until_complete(
                self._loop.create_connection(pf, sock=sock))
            self._close_fut = asyncio.Future(loop=self._loop)

    def send_notification(self, name, *args, **kwargs):
        if self._server_mode:
            raise Exception('invalid')
        self._protocol.send_notification(name, *args, **kwargs)

    def _handler(self, name, *args, **kwargs):
        raise NotImplementedError

    def _connection_lost(self, exc):
        if self._close_fut is not None:
            if exc is None:
                self._close_fut.set_result(None)
            else:
                self._close_fut.set_exception(exc)

    def wait_connection_close(self):
        if self._server_mode:
            raise Exception('invalid')
        self._loop.run_until_complete(self._close_fut)

    def close(self):
        if self._protocol:
            if self._server_mode:
                self._protocol.close()
                self._loop.run_until_complete(self._protocol.wait_closed())
            else:
                self._protocol.transport.close()
            self._protocol = None

    def close_sync(self):
        self.close()
        if not self._server_mode:
            self.wait_connection_close()
