"""Comprehensions: Listen und Dicts in einer Zeile."""

tickets = ["NL-101", "NL-111", "NL-104", "NL-118"]
numbers = [int(t[3:]) for t in tickets]
visible = [t for t in tickets if int(t[3:]) <= 110]
print(numbers)
print(visible)

prices = {"AKS-18": 89.90, "BIT-32": 12.50, "ZS-2": 6.95}
sale = {sku: round(p * 0.9, 2) for sku, p in prices.items()}
print(sale)
print(sum(p for p in prices.values() if p > 10))

errors = ["", "git fehlt", None]
print([e for e in errors if e])  # wie in Kapitel 2
