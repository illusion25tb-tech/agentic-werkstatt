"""Bedingungen und Schleifen."""

RATES = {"DE": 4.95, "AT": 9.90, "CH": 14.90}

for country, rate in RATES.items():
    if rate < 5:
        print(country, "günstig")
    elif rate < 10:
        print(country, "mittel")
    else:
        print(country, "teuer")

for ticket in ["NL-101", "NL-102", "NL-105", "NL-111"]:
    if ticket == "NL-102":
        continue  # schon erledigt, weiter zum nächsten
    if ticket == "NL-111":
        break  # ab NL-111 beginnt das Eval-Set
    print("bearbeite", ticket)

steps = 0
while steps < 3:  # ein Step-Budget von 3
    steps += 1
print("Schritte:", steps)
subtotal = 50.0
print("frei" if subtotal >= 50 else "kostet")
