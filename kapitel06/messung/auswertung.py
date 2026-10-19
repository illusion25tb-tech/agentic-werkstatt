"""Auswertung der Traces: erste Antwort (= ohne Verifizierer)
und Endergebnis (= mit Verifizierer). Aufruf aus messung/."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "solution"))
from evidence import Answer, check_claim
from tools import ROOT

for tr in sorted((Path(__file__).parent / "traces").glob("*.jsonl")):
    recs = [json.loads(z) for z in tr.read_text("utf-8").splitlines()]
    antworten = [r for r in recs if "answer" in r]
    calls = [r for r in recs if "tool" in r]
    zeile = {"run": tr.stem, "calls": len(calls),
             "tool_fehler": sum(1 for r in calls if r.get("error")),
             "antworten": len(antworten)}
    if antworten:
        raw = antworten[0]["answer"]
        try:
            a = Answer.model_validate_json(
                raw[raw.find("{"):raw.rfind("}") + 1])
            gr = [check_claim(c, ROOT) for c in a.claims]
            zeile.update(erste_json=True, claims=len(a.claims),
                         gueltig=sum(g is None for g in gr),
                         gruende=[g for g in gr if g],
                         pfade=[c.path for c in a.claims],
                         not_found=a.not_found)
        except Exception as e:  # noqa: BLE001
            zeile.update(erste_json=False, fehler=str(e)[:80])
    zeile["ende"] = "angenommen" if antworten and not antworten[
        -1]["rejected"] else next(
        (r["abort"] for r in recs if "abort" in r), "?")
    print(json.dumps(zeile, ensure_ascii=False))
