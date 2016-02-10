try:
    import asyncio
    try:
        from asyncio import ensure_future
    except ImportError:
        from asyncio import async as ensure_future
except ImportError:
    raise NotImplementedError('python2 currently not supported')

__all__ = ['asyncio', 'ensure_future']
