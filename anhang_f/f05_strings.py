"""f-Strings und Textmethoden."""

order = {"id": 4711, "total": 49.999999, "zip": " 01067 "}
print(f"Bestellung {order['id']}: {order['total']:.2f} EUR")
print(f"{order['zip']!r} wird zu {order['zip'].strip()!r}")
print(f"{int('01067')} {'Dresden'}")  # der Fehler aus NL-102

text = "NL-102\nPLZ ohne Null\nMeldung: Kundenservice"
rows = text.splitlines()
print(rows)
print(" | ".join(rows))
print(rows[0].startswith("NL-"), "Null" in rows[1])
print(rows[2].split(": "), rows[2].lower())
print("Bestellung 4711".replace("4711", "4712"))
