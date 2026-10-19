"""Zentrale Einstellungen des bestellservice.

Alle Werte sind Beispielwerte der fiktiven Firma. Sie sagen
nichts über reale Paketdienste oder Preise aus.
"""

SHOP_NAME = "Nordlicht Werkzeughandel GmbH"

# Absender auf jedem Versandlabel (fiktive Anschrift).
SENDER_LINES = (
    "Nordlicht Werkzeughandel GmbH",
    "Am Werkhof 12",
    "33602 Bielefeld",
)

# Umsatzsteuer in Prozent. Alle Katalogpreise sind brutto.
VAT_PERCENT = 19

# Länder, in die geliefert wird.
SUPPORTED_COUNTRIES = ("DE", "AT", "CH")

# Länge der Postleitzahl je Land.
POSTAL_CODE_LENGTH = {"DE": 5, "AT": 4, "CH": 4}

# Kundentypen. Geschäftskunden sehen Nettopreise.
CUSTOMER_TYPES = ("private", "business")

# Präfix für Sendungsnummern (siehe docs/paketfix).
TRACKING_PREFIX = "34"

# Höchstmenge je Warenkorbposition.
MAX_QUANTITY_PER_LINE = 99
