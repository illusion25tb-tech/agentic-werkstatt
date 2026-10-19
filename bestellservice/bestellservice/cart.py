"""Warenkorb: Positionen, Gutscheine, Summen."""

import sqlite3
from collections.abc import Callable
from datetime import datetime

from . import catalog
from .config import MAX_QUANTITY_PER_LINE, SUPPORTED_COUNTRIES
from .errors import NotFound, ValidationFailed
from .shipping_costs import (
    missing_for_free_shipping,
    shipping_cost,
)


def format_eur(amount: float) -> str:
    """Betrag im deutschen Format, z. B. 1.234,50 EUR."""
    text = f"{amount:,.2f}"
    text = text.replace(",", "X").replace(".", ",")
    return text.replace("X", ".") + " EUR"


def create_cart(
    conn: sqlite3.Connection,
    clock: Callable[[], datetime] = datetime.now,
) -> int:
    cur = conn.execute(
        "INSERT INTO carts (created_at) VALUES (?)",
        (clock().isoformat(timespec="seconds"),),
    )
    conn.commit()
    return cur.lastrowid


def _cart_row(conn: sqlite3.Connection, cart_id: int):
    row = conn.execute(
        "SELECT * FROM carts WHERE id = ?", (cart_id,)
    ).fetchone()
    if row is None:
        raise NotFound(f"Warenkorb {cart_id} existiert nicht")
    return row


def add_item(
    conn: sqlite3.Connection,
    cart_id: int,
    sku: str,
    quantity: int,
) -> int:
    """Legt eine Position in den Warenkorb.

    Jeder Aufruf erzeugt eine eigene Position, auch wenn der
    Artikel schon im Warenkorb liegt.
    """
    _cart_row(conn, cart_id)
    article = catalog.get_article(conn, sku)
    if not article.active:
        raise ValidationFailed(f"Artikel {sku} ist ausgelistet")
    if quantity < 1 or quantity > MAX_QUANTITY_PER_LINE:
        raise ValidationFailed(
            f"Menge muss zwischen 1 und "
            f"{MAX_QUANTITY_PER_LINE} liegen"
        )
    cur = conn.execute(
        "INSERT INTO cart_items (cart_id, sku, quantity) "
        "VALUES (?, ?, ?)",
        (cart_id, sku, quantity),
    )
    conn.commit()
    return cur.lastrowid


def remove_item(
    conn: sqlite3.Connection, cart_id: int, item_id: int
) -> None:
    _cart_row(conn, cart_id)
    cur = conn.execute(
        "DELETE FROM cart_items WHERE id = ? AND cart_id = ?",
        (item_id, cart_id),
    )
    if cur.rowcount == 0:
        raise NotFound(f"Position {item_id} nicht gefunden")
    conn.commit()


def apply_coupon(
    conn: sqlite3.Connection, cart_id: int, code: str
) -> dict:
    """Hinterlegt einen Gutscheincode am Warenkorb."""
    _cart_row(conn, cart_id)
    coupon = conn.execute(
        "SELECT * FROM coupons WHERE code = ?", (code,)
    ).fetchone()
    if coupon is None:
        raise ValidationFailed(f"Gutschein {code} ist ungültig")
    conn.execute(
        "UPDATE carts SET coupon_code = ? WHERE id = ?",
        (coupon["code"], cart_id),
    )
    conn.commit()
    return dict(coupon)


def cart_lines(
    conn: sqlite3.Connection, cart_id: int
) -> list[dict]:
    """Positionen mit Stückpreis, Gewicht und Zeilensumme."""
    _cart_row(conn, cart_id)
    rows = conn.execute(
        "SELECT * FROM cart_items WHERE cart_id = ? "
        "ORDER BY id",
        (cart_id,),
    ).fetchall()
    lines = []
    for row in rows:
        article = catalog.get_article(conn, row["sku"])
        price = catalog.unit_price(article, row["quantity"])
        lines.append(
            {
                "item_id": row["id"],
                "sku": article.sku,
                "name": article.name,
                "quantity": row["quantity"],
                "unit_price": price,
                "weight_kg": article.weight_kg,
                "line_total": round(price * row["quantity"], 2),
            }
        )
    return lines


def cart_subtotal(lines: list[dict]) -> float:
    """Warenwert aller Positionen in EUR."""
    subtotal = 0.0
    for line in lines:
        subtotal += line["unit_price"] * line["quantity"]
    return subtotal


def coupon_discount(coupon, subtotal: float) -> float:
    """Rabatt in EUR für einen Gutschein (oder 0)."""
    if coupon is None:
        return 0.0
    if subtotal < coupon["min_total"]:
        return 0.0
    if coupon["kind"] == "percent":
        return round(subtotal * coupon["value"] / 100, 2)
    return min(coupon["value"], subtotal)


def _coupon(conn: sqlite3.Connection, code: str | None):
    if not code:
        return None
    return conn.execute(
        "SELECT * FROM coupons WHERE code = ?", (code,)
    ).fetchone()


def cart_summary(
    conn: sqlite3.Connection,
    cart_id: int,
    country: str = "DE",
) -> dict:
    """Alles, was der Shop zum Warenkorb anzeigt."""
    if country not in SUPPORTED_COUNTRIES:
        raise ValidationFailed(
            f"Lieferland {country} wird nicht beliefert"
        )
    cart = _cart_row(conn, cart_id)
    lines = cart_lines(conn, cart_id)
    subtotal = cart_subtotal(lines)
    coupon = _coupon(conn, cart["coupon_code"])
    discount = coupon_discount(coupon, subtotal)
    goods_total = subtotal - discount
    shipping = (
        shipping_cost(goods_total, country) if lines else 0.0
    )
    total = goods_total + shipping
    return {
        "cart_id": cart_id,
        "country": country,
        "lines": lines,
        "coupon_code": cart["coupon_code"],
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "shipping": round(shipping, 2),
        "total": round(total, 2),
        "missing_for_free_shipping": missing_for_free_shipping(
            goods_total, country
        ),
        "display": {
            "subtotal": format_eur(subtotal),
            "shipping": format_eur(shipping),
            "total": format_eur(total),
        },
    }
