#!/bin/sh
# Rest der Ablation Kap. 8: rauschen F6 neu (3), vergiftet F1,F6 (6).
set -e
python - <<'PY'
import json, pathlib
p = pathlib.Path("ergebnisse.jsonl")
rows = [json.loads(z) for z in p.read_text(encoding="utf-8").splitlines()]
keep = [r for r in rows if not (r["bed"] == "rauschen" and r["frage"] == "F6")]
p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in keep), encoding="utf-8")
print(len(rows), "->", len(keep))
PY
for job in "rauschen F6" "vergiftet F1,F6"; do
  set -- $job
  PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf8 ../.venv/Scripts/python.exe run_ablation.py "$1" "$2" 3 >> ablation_v2.log 2>&1
done
wc -l ergebnisse.jsonl
