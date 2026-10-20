"""Personenbezug und Secrets aus Span-Attributen nehmen,
bevor sie gesetzt werden. Inhalte nur per Opt-in."""
import hashlib
import hmac
import os
import sys
from pathlib import Path

KAP11 = Path(__file__).resolve().parents[2] / "kapitel11"
sys.path.insert(0, str(KAP11 / "solution"))

from redact_secrets import redact, secret_values  # Kap. 11

PERSON = {"werkstatt.user", "werkstatt.approved_by",
          "werkstatt.commit_author"}
CONTENT = {"gen_ai.input.messages", "gen_ai.output.messages",
           "gen_ai.system_instructions",
           "gen_ai.tool.call.arguments",
           "gen_ai.tool.call.result"}
OPT_IN = "WERKSTATT_TRACE_CONTENT"


def pseudonym(value: str, key: bytes) -> str:
    """Gleiche Kennung, gleiches Pseudonym; ohne Schlüssel
    nicht zurückzurechnen (HMAC-SHA256)."""
    mac = hmac.new(key, value.encode("utf-8"), hashlib.sha256)
    return "p-" + mac.hexdigest()[:16]


def scrub(attrs: dict, key: bytes, environ=os.environ) -> dict:
    keep_content = environ.get(OPT_IN) == "1"
    secrets = secret_values(environ)    # Kapitel 11
    out = {}
    for k, v in attrs.items():
        if k in CONTENT and not keep_content:
            continue                    # Standard: weglassen
        if k in PERSON:
            v = pseudonym(str(v), key)
        elif isinstance(v, str):
            v = redact(v, secrets)
        out[k] = v
    return out
