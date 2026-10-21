"""Listen und Dicts: ein Warenkorb."""

lines = [
    {"sku": "AKS-18", "unit_price": 89.90, "quantity": 1},
    {"sku": "BIT-32", "unit_price": 12.50, "quantity": 2},
]
first = lines[0]
print(first["sku"], first["unit_price"])
print(first.get("coupon"), first.get("coupon", "ohne"))

lines.append({"sku": "ZS-2", "unit_price": 6.95, "quantity": 1})
print(len(lines), lines[-1]["sku"])

first["quantity"] = 2  # Wert ändern
print(lines[0])
print("sku" in first, "NL-104"[:2], [10, 20, 30][1:])
