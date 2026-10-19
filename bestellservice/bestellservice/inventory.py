"""Lagerbestand: verfügbare Menge, Reservierung, Freigabe.

`on_hand` ist die Menge im Regal, `reserved` die Menge, die
offenen Bestellungen zugeordnet ist. Verfügbar ist die
Differenz.
"""

import sqlite3

from .errors import NotFound, OutOfStock, ValidationFailed


def _row(conn: sqlite3.Connection, sku: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM stock WHERE sku = ?", (sku,)
    ).fetchone()
    if row is None:
        raise NotFound(f"Kein Lagerbestand für {sku}")
    return row


def available(conn: sqlite3.Connection, sku: str) -> int:
    row = _row(conn, sku)
    return row["on_hand"] - row["reserved"]


def stock_info(conn: sqlite3.Connection, sku: str) -> dict:
    row = _row(conn, sku)
    return {
        "sku": sku,
        "on_hand": row["on_hand"],
        "reserved": row["reserved"],
        "available": row["on_hand"] - row["reserved"],
    }


def set_on_hand(
    conn: sqlite3.Connection, sku: str, on_hand: int
) -> dict:
    """Setzt den gezählten Bestand (Inventur)."""
    row = _row(conn, sku)
    if on_hand < 0:
        raise ValidationFailed(
            "Bestand darf nicht negativ sein"
        )
    if on_hand < row["reserved"]:
        raise ValidationFailed(
            f"Bestand {on_hand} liegt unter der reservierten "
            f"Menge {row['reserved']}"
        )
    conn.execute(
        "UPDATE stock SET on_hand = ? WHERE sku = ?",
        (on_hand, sku),
    )
    conn.commit()
    return stock_info(conn, sku)


def check_lines(
    conn: sqlite3.Connection, lines: list[tuple[str, int]]
) -> None:
    """Prüft jede Position gegen den verfügbaren Bestand."""
    for sku, quantity in lines:
        free = available(conn, sku)
        if quantity > free:
            raise OutOfStock(
                f"Für {sku} sind nur {free} Stück verfügbar"
            )


def reserve(
    conn: sqlite3.Connection, lines: list[tuple[str, int]]
) -> None:
    """Reserviert Bestand für eine neue Bestellung."""
    check_lines(conn, lines)
    for sku, quantity in lines:
        conn.execute(
            "UPDATE stock SET reserved = reserved + ? "
            "WHERE sku = ?",
            (quantity, sku),
        )


def release(
    conn: sqlite3.Connection, lines: list[tuple[str, int]]
) -> None:
    """Gibt reservierten Bestand wieder frei."""
    for sku, quantity in lines:
        conn.execute(
            "UPDATE stock SET reserved = MAX(reserved - ?, 0) "
            "WHERE sku = ?",
            (quantity, sku),
        )


def ship(
    conn: sqlite3.Connection, lines: list[tuple[str, int]]
) -> None:
    """Bucht versendete Ware aus Regal und Reservierung aus."""
    for sku, quantity in lines:
        conn.execute(
            "UPDATE stock SET on_hand = on_hand - ?, "
            "reserved = reserved - ? WHERE sku = ?",
            (quantity, quantity, sku),
        )
