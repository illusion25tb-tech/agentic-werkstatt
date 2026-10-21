"""Ausnahmen abfangen und auslösen."""


class OrderError(Exception):
    """Fachlicher Fehler im Bestellservice."""


def parse_quantity(text: str) -> int:
    try:
        n = int(text)
    except ValueError:
        raise OrderError(f"keine Zahl: {text!r}") from None
    if n < 1:
        raise OrderError(f"Menge muss mindestens 1 sein: {n}")
    return n


for raw in ["3", "drei", "0"]:
    try:
        print("Menge:", parse_quantity(raw))
    except OrderError as e:
        print("FEHLER:", e)
