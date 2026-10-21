"""Sternchen: beliebig viele Argumente und Entpacken."""


def log(step: int, **data) -> None:
    print(step, data)


log(1, tool="read_file", path="cart.py")
args = {"tool": "run_tests", "path": "tests/"}
log(2, **args)


def total(*prices: float) -> float:
    return round(sum(prices), 2)


print(total(89.90, 12.50, 12.50))
first, *rest = ["NL-101", "NL-102", "NL-103"]
print(first, rest)
base = {"issue": "NL-104", "kategorie": "bug"}
print({**base, "prioritaet": "mittel"})
