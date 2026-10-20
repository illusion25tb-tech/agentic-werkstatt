"""Secrets: aus Kindprozessen fernhalten, aus Observations
und Trace-Zeilen schwärzen."""
import os
import re

NAME = re.compile(r"(?i)key|token|secret|passwor[dt]")
REGELN = [  # Muster ohne bekannten Wert, Heuristik
    (re.compile(r"(?i)(\w*(?:key|token|secret|passwor[dt])"
                r"\w*[\"']?\s*[:=]\s*[\"']?)"
                r"(?=[\w+/.=-]*\d)[\w+/.=-]{12,}"),
     r"\1[SECRET]"),
    (re.compile(r"(?i)(bearer\s+)[\w.=-]{12,}"), r"\1[SECRET]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[^-]*"),
     "[SECRET: PRIVATE KEY]"),
]
ERLAUBT = ("PATH", "SYSTEMROOT", "TEMP", "TMP", "HOME",
           "USERPROFILE", "LANG", "PYTHONUTF8")


def secret_values(environ=os.environ) -> list[str]:
    """Werte aller Variablen, die nach Secret heißen."""
    werte = {v for k, v in environ.items()
             if NAME.search(k) and len(v) >= 8}
    return sorted(werte, key=len, reverse=True)


def redact(text: str, secrets: list[str]) -> str:
    for s in secrets:                   # erst bekannte Werte
        text = text.replace(s, "[SECRET]")
    for muster, ersatz in REGELN:       # dann Muster
        text = muster.sub(ersatz, text)
    return text


def redact_obj(v, secrets: list[str]):
    """redact() für Trace-Zeilen mit Listen und Dicts."""
    if isinstance(v, str):
        return redact(v, secrets)
    if isinstance(v, dict):
        return {k: redact_obj(x, secrets) for k, x in v.items()}
    if isinstance(v, list):
        return [redact_obj(x, secrets) for x in v]
    return v


def leaks(args: dict, secrets: list[str]) -> bool:
    text = " ".join(str(v) for v in args.values())
    return redact(text, secrets) != text


def child_env(allow=ERLAUBT, environ=os.environ) -> dict:
    """Umgebung für Kindprozesse: nur, was erlaubt ist."""
    return {k: environ[k] for k in allow if k in environ}
