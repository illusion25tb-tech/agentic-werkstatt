"""Kosten- und Zeitbudget pro Run, Preise aus prices.toml."""
import time
import tomllib
from pathlib import Path

KAP10 = Path(__file__).resolve().parents[2] / "kapitel10"
PRICES = KAP10 / "solution" / "prices.toml"


class BudgetExceeded(Exception):
    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason, self.detail = reason, detail


class RunBudget:
    def __init__(self, model: str, max_cost: float,
                 max_seconds: float, prices: dict | None = None,
                 clock=time.monotonic):
        prices = prices or tomllib.loads(
            PRICES.read_text(encoding="utf-8"))
        p = prices["models"].get(model)
        if p is None:           # unbekannt ist nicht 0
            raise ValueError(f"Kein Preis für {model!r}")
        self.p_in, self.p_out = p["input"], p["output"]
        self.max_cost, self.max_seconds = max_cost, max_seconds
        self.clock, self.start = clock, clock()
        self.spent = 0.0

    def cost(self, t_in: int, t_out: int) -> float:
        """kosten() aus Kapitel 3, Preise je Mio. Token."""
        return (t_in * self.p_in + t_out * self.p_out) / 1e6

    def check_before(self, messages: list[dict]) -> None:
        sec = self.clock() - self.start
        if sec > self.max_seconds:
            raise BudgetExceeded("time_budget", f"{sec:.0f} s")
        chars = sum(len(m["content"]) for m in messages)
        est = self.spent + self.cost(chars // 4, 0)  # grob
        if est > self.max_cost:
            raise BudgetExceeded("cost_budget",
                                 f"geschätzt {est:.4f}")

    def add_usage(self, usage: dict) -> None:
        t_in = usage.get("prompt_tokens", 0)
        t_out = usage.get("completion_tokens", 0)
        self.spent += self.cost(t_in, t_out)
        if self.spent > self.max_cost:
            raise BudgetExceeded("cost_budget",
                                 f"{self.spent:.4f}")
