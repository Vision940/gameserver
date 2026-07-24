from __future__ import annotations


## Globals ##
_HANDLERS = {}


## Functions ##
def handles(req_type):
    """
    Register a handler for a request type.
    """

    def decorator(func):
        if req_type in _HANDLERS:
            raise RuntimeError(f"{req_type.__name__} already has a handler")
        _HANDLERS[req_type] = func
        return func

    return decorator


def get_handler(req: ApiReq):
    try:
        return _HANDLERS[type(req)]
    except KeyError as e:
        raise LookupError(f"No handler registered for {type(req).__name__}") from e


def handle(req: ApiReq):
    return get_handler(req)(req)

