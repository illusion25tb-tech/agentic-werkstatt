"""Werte, Variablen und Typen."""

order_id = "NL-4711"  # str: Text
quantity = 3  # int: ganze Zahl
unit_price = 13.70  # float: Kommazahl, mit Punkt
paid = True  # bool: True oder False
tracking = None  # None: (noch) kein Wert

print(type(order_id), type(quantity), type(paid))
print(quantity * unit_price)
print(round(quantity * unit_price, 2))
print(0.1 + 0.1 + 0.1 == 0.3)
print(tracking is None, 7 // 2, 7 % 2)
