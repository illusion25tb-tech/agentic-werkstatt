"""Synthetische Personendaten schwärzen, bevor etwas
ins Memory geht. Nur Stdlib."""
import re

NAMEN = ("Erika Musterfrau", "Max Mustermann")  # bekannte
REGELN = [
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[E-MAIL]"),
    (re.compile(r"(?<!\w)(?:\+49|0)[\d /-]{6,}\d"),
     "[TELEFON]"),
    (re.compile(r'("(?:name2?|strasse|avis_email)":\s*")'
                r'[^"]*"'), r'\1[GESCHWÄRZT]"'),
    (re.compile("|".join(map(re.escape, NAMEN))), "[NAME]"),
]


def redact(text: str) -> str:
    for muster, ersatz in REGELN:
        text = muster.sub(ersatz, text)
    return text
