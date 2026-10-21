"""Ein eigener Decorator, der Tool Calls protokolliert."""

import functools


def logged(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        print(f"-> {fn.__name__}{args}")
        result = fn(*args, **kwargs)
        print(f"<- {result!r}")
        return result

    return inner


@logged
def read_file(path: str) -> str:
    return f"(Inhalt von {path})"


read_file("cart.py")
print(read_file.__name__)
