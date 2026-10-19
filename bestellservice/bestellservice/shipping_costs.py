"""Versandkosten, die der Kunde im Warenkorb bezahlt.

Nicht zu verwechseln mit den Tarifen, die Nordlicht an den
Versanddienstleister zahlt (siehe tariffs.py).
"""

# Versandkosten je Lieferland in EUR (brutto).
RATES = {
    "DE": 4.95,
    "AT": 9.90,
    "CH": 14.90,
}

# Versandkostenfrei ab diesem Warenwert, nur Inland.
FREE_SHIPPING_FROM = 50.0


def shipping_cost(
    subtotal: float, country: str = "DE"
) -> float:
    """Versandkosten für einen Warenwert in EUR.

    `subtotal` ist der Warenwert nach Rabatt.
    """
    rate = RATES.get(country.lower(), RATES["DE"])
    if country == "DE" and subtotal > FREE_SHIPPING_FROM:
        return 0.0
    return rate


def missing_for_free_shipping(
    subtotal: float, country: str = "DE"
) -> float | None:
    """Betrag, der zur Versandkostenfreiheit noch fehlt.

    Gibt None zurück, wenn es im Lieferland keine
    Versandkostenfreiheit gibt.
    """
    if country != "DE":
        return None
    missing = FREE_SHIPPING_FROM - subtotal
    return round(max(missing, 0.0), 2)
