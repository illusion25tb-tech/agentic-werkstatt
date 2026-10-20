"""Observations mit Herkunft einrahmen (Spotlighting)."""
import re

RAHMEN = re.compile(r"<{3,}|>{3,}")     # Imitate des Rahmens
UNSICHTBAR = re.compile(                 # Tags, Nullbreite
    "[\U000E0000-\U000E007F\u200b-\u200f\u2060-\u2064\ufeff]")


def wrap(obs: str, source: str, trusted: bool) -> str:
    """Rahmt obs ein. Hilft dem Modell, schützt aber nicht."""
    text, n = UNSICHTBAR.subn("", obs)
    text = RAHMEN.sub("[entfernt]", text)
    source = re.sub(r'[\s"]+', " ", UNSICHTBAR.sub("", source))
    source = RAHMEN.sub("", source)
    stufe = "eigen" if trusted else "fremd"
    note = f"\n[{n} unsichtbare Zeichen entfernt]" if n else ""
    return (f'<<<DATEN quelle="{source}" vertrauen="{stufe}">>>'
            f"\n{text}{note}\n<<<ENDE DATEN>>>")
