import os
import sys
import time
from pathlib import Path

os.environ["PYDANTIC_AI_NO_BANNER"] = "1"
SOL = Path(r"C:\Users\ToertjeB\CLAUDE\Bücher\#36 B_Durchstarten mit Agentic Coding\code\kapitel09\solution")
sys.path.insert(0, str(SOL))
import agent as A
import cli
from deps import Deps
from diff_budget import Budget
from policy import Policy
from pydantic_ai import Agent, NativeOutput

repo = Path(sys.argv[1])
d = Deps(repo, Policy("eval"), None, Budget([], []), Path(sys.argv[2]))
ag = Agent(deps_type=Deps, output_type=NativeOutput(A.Plan),
           instructions=A.instructions, retries=3,
           tools=[A.guarded(f) for f in A.READ])
t = time.time()
r = ag.run_sync("Ticket: Label für 38 kg hat Standardtarif XL statt "
                "Sperrgut. Finde die Ursache und schlage einen Plan vor.",
                deps=d, model=cli.model_from_env(), usage_limits=A.LIMITS)
print(round(time.time() - t), r.output, r.usage)
print(Path(sys.argv[2]).read_text(encoding="utf-8")[:2000])
