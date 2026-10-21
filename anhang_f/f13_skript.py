"""Versandkosten für Warenwerte von der Kommandozeile."""

import sys

from versand import shipping_cost


def main(argv: list[str]) -> int:
    if not argv:
        print("Bitte Warenwerte angeben.", file=sys.stderr)
        return 2
    for value in argv:
        cost = shipping_cost(float(value))
        print(f"{value} EUR -> Versand {cost:.2f} EUR")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
