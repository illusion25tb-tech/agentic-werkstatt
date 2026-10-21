"""Mengen, lambda und Sortieren."""

read = {"cart.py", "orders.py"}
read.add("cart.py")  # schon drin: ändert nichts
expected = {"cart.py", "shipping_costs.py"}
print(len(read))
print(read & expected)  # in beiden
print(expected - read)  # erwartet, aber nie gelesen

hits = [(3, "cart.py"), (7, "orders.py"), (5, "invoice.py")]
hits.sort(key=lambda t: -t[0])  # meiste Treffer zuerst
print(hits)
print(sorted(["NL-110", "NL-102", "NL-107"]))
print(max(hits, key=lambda t: t[0])[1])
