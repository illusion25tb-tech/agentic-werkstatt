"""Versandkosten für den Warenkorb (vereinfacht)."""

RATES = {"DE": 4.95, "AT": 9.90, "CH": 14.90}
FREE_SHIPPING_FROM = 50.0


def shipping_cost(
    subtotal: float, country: str = "DE"
) -> float:
    """Versandkosten in EUR für einen Warenwert."""
    if country not in RATES:
        raise ValueError(f"kein Versand nach {country}")
    if country == "DE" and subtotal >= FREE_SHIPPING_FROM:
        return 0.0
    return RATES[country]


def first_open(tickets: list[str]) -> str | None:
    for ticket in tickets:
        if not ticket.endswith("erledigt"):
            return ticket
    return None


if __name__ == "__main__":  # erklärt im Abschnitt Skripte
    print(shipping_cost(49.99), shipping_cost(50.0))
    print(shipping_cost(80.0, country="AT"))
    print(first_open(["NL-101 erledigt", "NL-102"]))
    print(first_open([]))
