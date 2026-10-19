"""Messung Tokens: derselbe Inhalt deutsch und englisch, prompt_tokens aus LAST_USAGE.

Overhead (Chat-Template, System-Prompt) wird mit leerer Nutzernachricht gemessen und abgezogen.
"""
import json, os, sys, time
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "solution"))
import llm
llm.TIMEOUT = 900

TEXTE = {
    "satz": (
        "Die Bestellbestätigung zeigt bei manchen Geschäftskunden einen anderen Betrag als die Rechnung.",
        "For some business customers, the order confirmation shows a different amount than the invoice.",
    ),
    "absatz": (
        "Hallo zusammen, ein Kunde hat sich gemeldet, der Betrag in der Bestätigungsmail passt nicht "
        "zu dem, was er bezahlt hat. Ich glaube, es war ein Firmenkunde, bin mir aber nicht ganz sicher, "
        "die Mail habe ich nicht mehr. Bei mir selbst sieht die Bestätigung richtig aus.",
        "Hi everyone, a customer got in touch: the amount in the confirmation email does not match "
        "what he paid. I think it was a business customer, but I am not completely sure, I no longer "
        "have the email. On my side the confirmation looks correct.",
    ),
    "komposita": (
        "Versandkostenfreigrenze, Sperrguttarif, Bestellbestätigungsmail, Lagerbestandsprüfung",
        "free shipping threshold, bulky goods rate, order confirmation email, stock level check",
    ),
}
SYSTEM = "Antworte nur mit OK."
os.environ.update(LLM_BASE_URL="http://127.0.0.1:11434/v1", LLM_JSON_MODE="0", LLM_TEMPERATURE="0")

def tokens(model, text):
    os.environ["LLM_MODEL"] = model
    llm.ask_model([{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}])
    return llm.LAST_USAGE["prompt_tokens"]

with (HERE / "tokens_de_en.jsonl").open("w", encoding="utf-8") as f:
    for model in ["gemma3:4b", "llama3.2:3b", "phi4-mini"]:
        base = tokens(model, "")
        for name, (de, en) in TEXTE.items():
            t_de, t_en = tokens(model, de) - base, tokens(model, en) - base
            rec = {"model": model, "text": name, "woerter_de": len(de.split()), "woerter_en": len(en.split()),
                   "zeichen_de": len(de), "zeichen_en": len(en),
                   "tokens_de": t_de, "tokens_en": t_en, "faktor": round(t_de / t_en, 2),
                   "overhead": base, "ts": time.strftime("%Y-%m-%d %H:%M")}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
            print(rec, flush=True)
        # eine Quelldatei aus dem bestellservice
        src = (HERE.parents[1] / "bestellservice/bestellservice/cart.py").read_text(encoding="utf-8")
        t = tokens(model, src) - base
        rec = {"model": model, "text": "cart.py", "zeilen": len(src.splitlines()), "zeichen": len(src),
               "tokens": t, "ts": time.strftime("%Y-%m-%d %H:%M")}
        f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
        print(rec, flush=True)
