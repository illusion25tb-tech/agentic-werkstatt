"""Versandtarife beim Versanddienstleister PaketFix.

Das sind die Preise, die Nordlicht pro Paket an PaketFix
zahlt, nicht die Versandkosten des Kunden. Gewichtsklassen
und Produktcodes stehen in docs/paketfix/paketfix_api_v2.md.
"""

from dataclasses import dataclass

from .errors import ValidationFailed


@dataclass(frozen=True)
class Tariff:
    code: str
    name: str
    max_kg: float
    price: float


TARIFFS = {
    "S": Tariff("PF-STD-S", "Standard S", 5.0, 4.10),
    "M": Tariff("PF-STD-M", "Standard M", 10.0, 5.60),
    "L": Tariff("PF-STD-L", "Standard L", 20.0, 8.30),
    "XL": Tariff("PF-STD-XL", "Standard XL", 31.5, 11.90),
    "SPERRGUT": Tariff("PF-SPG", "Sperrgut", 60.0, 29.90),
}

# Reihenfolge, in der die Gewichtsklassen geprüft werden.
WEIGHT_CLASSES = ("S", "M", "L", "XL")

# Über diesem Gewicht gilt eine Sendung als Sperrgut.
BULKY_FROM_KG = 31.5

# Schwerere Sendungen gehen per Spedition, nicht per Paket.
MAX_PARCEL_KG = 60.0


def is_bulky(weight_kg: float) -> bool:
    return weight_kg > BULKY_FROM_KG


def weight_class(weight_kg: float) -> str:
    """Gewichtsklasse für ein Paketgewicht in kg."""
    if weight_kg <= 0:
        raise ValidationFailed("Gewicht muss positiv sein")
    for code in WEIGHT_CLASSES:
        if weight_kg <= TARIFFS[code].max_kg:
            return code
    # Schwerer geht es nur noch in die größte Klasse.
    return "XL"


def tariff_for(weight_kg: float) -> Tariff:
    """Tarif für ein Paket mit dem angegebenen Gewicht."""
    if weight_kg > MAX_PARCEL_KG:
        raise ValidationFailed(
            f"{weight_kg:.1f} kg: Versand nur per Spedition"
        )
    return TARIFFS[weight_class(weight_kg)]
