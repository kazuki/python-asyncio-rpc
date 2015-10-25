try:
    import asyncio
except ImportError:
    import trollius as asyncio

try:
    from asyncio import ensure_future
except ImportError:
    from asyncio import async as ensure_future

__all__ = ['asyncio', 'ensure_future']
