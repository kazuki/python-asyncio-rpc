import sys
import time

from asynciorpc import asyncio
from asynciorpc.client import Client
from asynciorpc.server import Server

addr = '127.0.0.1'
port = 8888
loop = asyncio.get_event_loop()


def run_server():
    class EchoServer(Server):
        def _handler(self, name, *args, **kwargs):
            return args[0]

    if True:
        server = EchoServer(addr, port)
        print('running server...')
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
    else:
        import socket
        server = socket.socket()
        server.bind((addr, port))
        server.listen(1)
        while True:
            try:
                s = EchoServer(sock=server.accept()[0])
                s.wait_connection_close()
            except KeyboardInterrupt:
                break
            finally:
                s.close_sync()
    server.close()
    loop.stop()
    loop.close()


def bench_client(rpc_type):
    N = 1
    client = Client(addr, port, rpc_type=rpc_type)

    start = time.time()
    for i in range(N):
        client.call('echo', i)
    end = time.time()
    delta = end - start
    print("  sync: {0:.0f} qps".format(N / delta))

    futures = []
    start = time.time()
    for i in range(N):
        futures.append(client.call_async('echo', i))
    for fut in futures:
        loop.run_until_complete(fut)
    end = time.time()
    delta = end - start
    print("  async: {0:.0f} qps".format(N / delta))

    start = time.time()
    for i in range(N):
        client.notify('notify', i)
    client.call('echo', 0)
    end = time.time()
    delta = end - start
    print("  notify: {0:.0f} qps".format(N / delta))

    client.close_sync()

def run_client():
    print('JSON-RPC 2.0')
    bench_client('json')
    print('msgpack-rpc')
    bench_client('msgpack')
    loop.stop()
    loop.close()


def main():
    if sys.argv[1] == 'server':
        run_server()
    else:
        run_client()


main()
