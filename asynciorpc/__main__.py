import sys
import time

from asynciorpc import asyncio
from asynciorpc.client import Client
from asynciorpc.server import Server

addr = '127.0.0.1'
port = 8888
loop = asyncio.get_event_loop()


def run_server():
    server = Server(addr, port)
    print('running server...')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    server.close()
    loop.run_until_complete(asyncio.sleep(0))
    loop.stop()
    loop.close()


def run_client():
    N = 10000
    client = Client(addr, port, rpc_type='msgpack')

    start = time.time()
    for i in range(N):
        client.call('echo', i)
    end = time.time()
    delta = end - start
    print("sync: {0} qps".format(N / delta))

    futures = []
    start = time.time()
    for i in range(N):
        futures.append(client.call_async('echo', i))
    for fut in futures:
        loop.run_until_complete(fut)
    end = time.time()
    delta = end - start
    print("async: {0} qps".format(N / delta))

    client.close()
    loop.run_until_complete(asyncio.sleep(0))
    loop.stop()
    loop.close()


def main():
    if sys.argv[1] == 'server':
        run_server()
    else:
        run_client()


main()
