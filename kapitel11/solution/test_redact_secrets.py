import subprocess
import sys

from conftest import KEY
from redact_secrets import (
    child_env,
    leaks,
    redact,
    secret_values,
)

ENV = {"PAKETFIX_KEY": KEY, "LLM_API_KEY": "sk-attrappe-123456",
       "PATH": "/usr/bin", "LLM_MODEL": "llama3.2-16k"}


def test_bekannte_werte_aus_der_umgebung():
    werte = secret_values(ENV)
    assert set(werte) == {KEY, "sk-attrappe-123456"}
    text = f"Fehler: Schlüssel {KEY} ungültig"
    assert redact(text, werte) == \
        "Fehler: Schlüssel [SECRET] ungültig"


def test_muster_ohne_bekannten_wert():
    text = ("X-PaketFix-Key: a8f3k2m9q7w1z5x0c4v6\n"
            'token = "ghx_1234567890abcdef"\n'
            "Authorization: Bearer abc.def.1234567890")
    out = redact(text, [])
    assert "a8f3k2m9q7w1z5x0c4v6" not in out
    assert "1234567890abcdef" not in out
    assert out.count("[SECRET]") == 3


def test_normaler_code_bleibt_unveraendert():
    code = ('key = os.environ["PAKETFIX_KEY"]\n'
            "headers = {'X-PaketFix-Key': key}\n"
            "MAX_TOKENS = 2000\n"
            "def tariff_for(kg: float) -> Tariff:\n")
    assert redact(code, [KEY]) == code


def test_leaks_findet_secret_in_argumenten():
    assert leaks({"content": f"# {KEY}"}, [KEY])
    assert not leaks({"content": "def test_x(): pass"}, [KEY])


def kind(**kw) -> str:
    code = "import os; print(os.environ.get('PAKETFIX_KEY'))"
    p = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True,
                       check=True, **kw)
    return p.stdout.strip()


def test_kindprozess_sieht_nur_die_allowlist(monkeypatch):
    monkeypatch.setenv("PAKETFIX_KEY", KEY)
    assert kind() == KEY                # erbt alles
    assert kind(env=child_env()) == "None"
    assert "PATH" in child_env()
