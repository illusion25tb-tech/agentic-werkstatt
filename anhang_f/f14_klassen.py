class BudgetExceeded(Exception):
    pass


class StepBudget:
    def __init__(self, max_steps: int) -> None:
        self.max_steps = max_steps
        self.used = 0

    def spend(self) -> int:
        if self.used >= self.max_steps:
            raise BudgetExceeded(
                f"{self.max_steps} Schritte verbraucht")
        self.used += 1
        return self.max_steps - self.used


budget = StepBudget(2)
print(budget.spend(), budget.spend())
try:
    budget.spend()
except BudgetExceeded as e:
    print("Abbruch:", e)
