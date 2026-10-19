"""Sendungsnummern im PaketFix-Format.

Aufbau: Präfix (2 Ziffern), laufende Nummer (10 Ziffern),
Prüfziffer (1 Ziffer), zusammen 13 Ziffern.
"""

from .config import TRACKING_PREFIX
from .errors import ValidationFailed

LENGTH = 13


def check_digit(base: str) -> int:
    """Prüfziffer nach Modulo 10 mit den Gewichten 3 und 1."""
    if not base.isdigit():
        raise ValidationFailed("Nur Ziffern erlaubt")
    total = 0
    for index, char in enumerate(base):
        weight = 3 if index % 2 == 0 else 1
        total += int(char) * weight
    return (10 - total % 10) % 10


def make_tracking_number(serial: int) -> str:
    """Sendungsnummer aus einer laufenden Nummer."""
    if serial < 0 or serial >= 10**10:
        raise ValidationFailed("Laufende Nummer ungültig")
    base = f"{TRACKING_PREFIX}{serial:010d}"
    return base + str(check_digit(base))


def is_valid(number: str) -> bool:
    number = number.replace(" ", "")
    if len(number) != LENGTH or not number.isdigit():
        return False
    return check_digit(number[:-1]) == int(number[-1])


def pretty(number: str) -> str:
    """Lesbare Schreibweise in Vierergruppen."""
    groups = [
        number[i : i + 4] for i in range(0, len(number), 4)
    ]
    return " ".join(groups)
