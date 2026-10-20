"""Erfolgsquote, pass@k, pass^k und Wilson-Intervall."""
from math import comb, sqrt


def pass_at_k(n: int, c: int, k: int) -> float:
    """Chen et al. 2021: Chance, dass von k aus n Runs mit c
    Erfolgen mindestens einer gelingt."""
    if n - c < k:
        return 1.0
    return 1 - comb(n - c, k) / comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """Yao et al. 2024, pass^k: Chance, dass alle k Runs
    gelingen. Die strenge Sicht für unbeaufsichtigte Agenten."""
    return comb(c, k) / comb(n, k)


def wilson(s: int, n: int,
           z: float = 1.96) -> tuple[float, float]:
    """95-%-Intervall für die Quote s/n nach Wilson (1927)."""
    if n == 0:
        return (0.0, 1.0)
    p = s / n
    mitte = p + z * z / (2 * n)
    rand = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    nenner = 1 + z * z / n
    return (max(0.0, (mitte - rand) / nenner),
            min(1.0, (mitte + rand) / nenner))
