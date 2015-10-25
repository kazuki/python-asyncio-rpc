from asynciorpc import asyncio
from asynciorpc.rpc import ServerRpc


class Server(object):
    def __init__(self, addr, port):
        self._loop = asyncio.get_event_loop()
        self._protocol = self._loop.run_until_complete(
            self._loop.create_server(lambda: ServerRpc(self._handler),
                                     addr, port))

    def _handler(self, name, *args, **kwargs):
        return args[0]

    def close(self):
        if self._protocol:
            self._protocol.close()
            self._loop.run_until_complete(self._protocol.wait_closed())
            self._protocol = None
