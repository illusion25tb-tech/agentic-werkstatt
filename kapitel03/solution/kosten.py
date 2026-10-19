"""Was ein Aufruf kostet: Tokens mal Preis."""


def kosten(usage: dict, preis_in: float,
           preis_out: float) -> float:
    """Preise je Million Tokens; Ergebnis in deren Währung."""
    t_in = usage.get("prompt_tokens", 0)
    t_out = usage.get("completion_tokens", 0)
    return (t_in * preis_in + t_out * preis_out) / 1_000_000
