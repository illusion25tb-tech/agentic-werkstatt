from contextlib import contextmanager


def ticket_ids(start: int, end: int):
    for n in range(start, end + 1):
        yield f"NL-{n}"


gen = ticket_ids(101, 103)
print(next(gen))
print(list(gen))


@contextmanager
def workspace(name: str):
    print("lege an:", name)
    try:
        yield name
    finally:
        print("räume auf:", name)


with workspace("butler/NL-107") as ws:
    print("arbeite in", ws)
