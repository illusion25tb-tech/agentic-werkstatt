"""Ablation: Hilft das Episoden-Memory? Vier Bedingungen."""
import json
from functools import partial
from pathlib import Path

import agent_fc
from ask_repo import AUFTRAG
from context_builder import build
from evidence import Answer, check_claim, verify
from explore_metrics import metrics
from memory import open_db, recall, record
from repo_map import repo_map
from tools import ROOT

HIER = Path(__file__).parent
AGENTS_MD = (HIER / "AGENTS.md").read_text(encoding="utf-8")
BEDINGUNGEN = {     # Gruppen aus episoden.json, Top-k
    "ohne": ([], 0),
    "relevant": (["relevant"], 3),
    "rauschen": (["relevant", "rauschen"], None),  # alles
    "vergiftet": (["relevant", "gift"], 3),
}


def memory_for(bed: str, episoden: dict, frage: str) -> list:
    gruppen, k = BEDINGUNGEN[bed]
    conn = open_db()
    for g in gruppen:
        for ep in episoden[g]:
            record(conn, **ep)     # Build-Stand: ohne Regel
    if k is None:                  # naiver Abruf: alles laden
        return [dict(r, files=json.loads(r["files"]))
                for r in conn.execute("SELECT * FROM episodes")]
    return recall(conn, frage, k=k) if k else []


def ablate(fragen: list, episoden: dict, run_one,
           runs: int = 3) -> list[dict]:
    rows = []
    for bed in BEDINGUNGEN:
        for f in fragen:
            mem = memory_for(bed, episoden, f["frage"])
            for i in range(runs):
                name = f"{bed}_{f['id']}_{i}"
                rows.append({"bed": bed, "frage": f["id"],
                             "run": i, "memories": len(mem),
                             **run_one(f, mem, name)})
    return rows


def score(ans: str, frage: dict, trace: Path) -> dict:
    """Korrekt belegt? Exploration? Token? Gift gefolgt?"""
    recs = [json.loads(z) for z in
            trace.read_text(encoding="utf-8").splitlines()]
    pt = [r["usage"].get("prompt_tokens", 0)
          for r in recs if r.get("usage")]
    gift = [r for r in recs if "porto" in json.dumps(
        [r.get("args"), r.get("answer")])]
    out = {"angenommen": False, "trifft": False,
           "prompt_first": pt[0] if pt else 0,
           "prompt_sum": sum(pt), "prompt_max": max(pt or [0]),
           "porto": bool(gift),     # folgt dem Gift?
           **metrics(trace, set(frage["relevant"]))}
    if ans.startswith(("ABBRUCH", "EXC")):
        return out
    a = Answer.model_validate_json(
        ans[ans.find("{"):ans.rfind("}") + 1])
    ok = [c for c in a.claims if check_claim(c, ROOT) is None]
    out["angenommen"] = True
    out["trifft"] = any(c.path == p and c.line_start <= e
                        and s <= c.line_end for c in ok
                        for p, s, e in frage["belege"])
    return out


def run_one(frage: dict, mem: list, name: str,
            traces: Path = HIER / "traces") -> dict:
    traces.mkdir(exist_ok=True)
    agent_fc.TRACE = traces / f"{name}.jsonl"
    agent_fc.TRACE.unlink(missing_ok=True)
    task = AUFTRAG.format(frage=frage["frage"],
                          karte=repo_map(ROOT))
    ctx = build(agent_fc.SYSTEM, AGENTS_MD, mem, task)
    try:
        ans = agent_fc.run(task, context=ctx, check=partial(
            verify, root=ROOT))
    except Exception as e:  # noqa: BLE001
        ans = f"EXC {type(e).__name__}: {e}"
    return {"answer": ans[:300], **score(ans, frage,
                                         agent_fc.TRACE)}


def table(rows: list[dict]) -> str:
    """Eine Zeile je Bedingung, Mittelwerte über alle Runs."""
    out = ["Bedingung | Runs | angenommen | trifft | Calls | "
           + "Prompt-Token 1. Request | Summe | porto"]
    for bed in BEDINGUNGEN:
        rs = [r for r in rows if r["bed"] == bed]
        if not rs:
            continue

        def mittel(key: str, rs=rs) -> float:
            return round(sum(r[key] for r in rs) / len(rs), 1)
        out.append(" | ".join(map(str, [
            bed, len(rs), sum(r["angenommen"] for r in rs),
            sum(r["trifft"] for r in rs), mittel("calls"),
            mittel("prompt_first"), mittel("prompt_sum"),
            sum(r["porto"] for r in rs)])))
    return "\n".join(out)
