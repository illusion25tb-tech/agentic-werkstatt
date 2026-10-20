"""python fault_matrix.py starter|solution

Nachgestellt (geskriptete Rollen, kein Modell): spielt jede
Störung aus faults.yaml ein und zeigt, ob der Capstone sie
erkennt, also eskaliert statt zu empfehlen."""
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent / sys.argv[1]))

from capstone import release, security_review
from conftest import DIFF
from inject import inject, load

ROLES = {"planner": lambda i: "bestellservice/tariffs.py",
         "implementer": lambda p: DIFF,
         "tester": lambda d: True,
         "security": security_review,
         "release_reviewer": lambda d: "Empfehlung: freigeben"}

faults = load(HIER.parent / sys.argv[1] / "faults.yaml")
erkannt = 0
for f in faults:
    out = release("NL-107", inject(ROLES, f))
    erkannt += out.result == "eskalation"
    print(f"{f.id:13} {out.result:10} {out.reason}")
print(f"erkannt: {erkannt} von {len(faults)}")
