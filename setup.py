import os
from setuptools import setup, find_packages
import sys

install_requires = []
if not (sys.version_info.major == 3 and sys.version_info.minor >= 4):
    install_requires.append('trollius==2.0')

setup(
    name='python-asyncio-rpc',
    version = '0.0.1',
    description='jsonrpc/msgpack-rpc with asyncio',
    author='Kazuki Oikawa',
    author_email='k@oikw.org',
    packages = find_packages(exclude=[]),
    install_requires = install_requires
)
