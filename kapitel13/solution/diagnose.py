"""python diagnose.py trace.jsonl ...

Sucht in Traces der Kapitel 9 bis 12 die Signaturen
bekannter Fehlerbilder. Meldet Zeile, Bild und Beleg."""
import json
import sys
from pathlib import Path

CONTEXT = 16_384            # num_ctx von llama3.2-16k
SERIE = 3                   # ab so vielen gleichen in Folge


def diagnose(lines: list[str]) -> list[tuple[int, str, str]]:
    out, last, streak, pol, rej = [], None, 0, 0, 0
    read = {}                       # Rolle, Runde -> Tool Calls
    for n, line in enumerate(lines, 1):
        r = json.loads(line)
        if r.get("peak_input", 0) > 0.75 * CONTEXT:
            out.append((n, "Kontext fast voll",
                        f"{r['peak_input']} Token"))
        if r.get("approve") and not read.get(
                ("reviewer", r.get("round"))):
            out.append((n, "Freigabe ohne Lesen",
                        r.get("reason", "")[:60]))
        if any(k.endswith("_rejected") for k in r):
            rej += 1                # Plan, Bericht, Urteil
            if rej == SERIE:
                out.append((n, "Vertrag verfehlt in Serie",
                            str(list(r.values())[-1])[:60]))
        if "tool" not in r:
            continue
        rr = (r.get("role"), r.get("round"))
        read[rr] = read.get(rr, 0) + 1
        obs = r["obs"]
        if not obs.strip():
            out.append((n, "leere Observation", r["tool"]))
        if "Timeout" in obs:
            out.append((n, "Tool-Timeout", obs[:60]))
        key = (r["tool"], json.dumps(r["args"]), obs)
        streak = streak + 1 if key == last else 1
        last = key
        if streak == SERIE:
            out.append((n, "Wiederholung ohne Fortschritt",
                        r["tool"]))
        policy = obs.startswith("FEHLER [policy]")
        pol = pol + 1 if policy else 0
        if pol == SERIE:
            out.append((n, "Policy-Blockade in Serie",
                        obs[:60]))
    return out


if __name__ == "__main__":
    for p in map(Path, sys.argv[1:]):
        lines = p.read_text(encoding="utf-8").splitlines()
        for n, bild, beleg in diagnose(lines):
            print(f"{p}:{n}  {bild}: {beleg}")
