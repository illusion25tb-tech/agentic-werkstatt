"""Bestellungen: Anlage, Abruf, Status, Bestätigung, Export.

Hinweis: Dieses Modul ist über die Jahre gewachsen und
enthält inzwischen auch Validierung, Texte für den
Kundenservice und den CSV-Export für die Buchhaltung.
"""

import csv
import io
import sqlite3
from collections.abc import Callable
from datetime import datetime

from . import cart, inventory, labels, tariffs
from .config import (
    CUSTOMER_TYPES,
    POSTAL_CODE_LENGTH,
    SHOP_NAME,
    SUPPORTED_COUNTRIES,
    VAT_PERCENT,
)
from .errors import (
    InvalidState,
    NotFound,
    ValidationFailed,
)

# Statuswerte einer Bestellung.
STATUS_NEW = "new"
STATUS_PAID = "paid"
STATUS_PAYMENT_FAILED = "payment_failed"
STATUS_SHIPPED = "shipped"

STATUSES = (
    STATUS_NEW,
    STATUS_PAID,
    STATUS_PAYMENT_FAILED,
    STATUS_SHIPPED,
)

# Erlaubte Statuswechsel.
TRANSITIONS = {
    STATUS_NEW: {STATUS_PAID, STATUS_PAYMENT_FAILED},
    STATUS_PAID: {STATUS_SHIPPED},
    STATUS_PAYMENT_FAILED: set(),
    STATUS_SHIPPED: set(),
}

# Datumsformat, das der Kundenservice in der Liste sieht.
DATE_FORMAT = "%d.%m.%Y %H:%M:%S"


# ------------------------------------------------------------
# Validierung
# ------------------------------------------------------------


def validate_customer(customer: dict) -> dict:
    name = (customer.get("name") or "").strip()
    email = (customer.get("email") or "").strip()
    kind = customer.get("type") or "private"
    if not name:
        raise ValidationFailed("Kundenname fehlt")
    if "@" not in email or email.startswith("@"):
        raise ValidationFailed(f"E-Mail {email!r} ist ungültig")
    if kind not in CUSTOMER_TYPES:
        raise ValidationFailed(f"Kundentyp {kind!r} unbekannt")
    return {"name": name, "email": email, "type": kind}


def validate_address(address: dict) -> dict:
    country = (address.get("country") or "DE").upper()
    if country not in SUPPORTED_COUNTRIES:
        raise ValidationFailed(
            f"Lieferland {country} wird nicht beliefert"
        )
    postal = (address.get("postal_code") or "").strip()
    length = POSTAL_CODE_LENGTH[country]
    if not postal.isdigit() or len(postal) != length:
        raise ValidationFailed(
            f"Postleitzahl {postal!r} passt nicht zu {country}"
        )
    result = {"country": country, "postal_code": postal}
    for field in ("name", "street", "city"):
        value = (address.get(field) or "").strip()
        if not value:
            raise ValidationFailed(f"Adressfeld {field} fehlt")
        result[field] = value
    return result


# ------------------------------------------------------------
# Lesen
# ------------------------------------------------------------


def _order_row(conn: sqlite3.Connection, order_id: int):
    row = conn.execute(
        "SELECT * FROM orders WHERE id = ?", (order_id,)
    ).fetchone()
    if row is None:
        raise NotFound(f"Bestellung {order_id} existiert nicht")
    return row


def _items(conn: sqlite3.Connection, order_id: int) -> list:
    rows = conn.execute(
        "SELECT sku, name, quantity, unit_price, weight_kg "
        "FROM order_items WHERE order_id = ? ORDER BY id",
        (order_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def _lines(items: list[dict]) -> list[tuple[str, int]]:
    return [(i["sku"], i["quantity"]) for i in items]


def get_order(conn: sqlite3.Connection, order_id: int) -> dict:
    order = dict(_order_row(conn, order_id))
    order["items"] = _items(conn, order_id)
    order["weight_kg"] = order_weight(order["items"])
    order["bulky"] = tariffs.is_bulky(order["weight_kg"])
    label = conn.execute(
        "SELECT tracking_number FROM labels WHERE order_id = ?",
        (order_id,),
    ).fetchone()
    order["tracking_number"] = (
        label["tracking_number"] if label else None
    )
    return order


def list_orders(conn: sqlite3.Connection) -> list[dict]:
    """Alle Bestellungen, neueste zuerst."""
    rows = conn.execute(
        "SELECT id, customer_name, status, total, created_at "
        "FROM orders"
    ).fetchall()
    result = [dict(r) for r in rows]
    result.sort(key=lambda o: o["created_at"], reverse=True)
    return result


def order_weight(items: list[dict]) -> float:
    """Gesamtgewicht einer Bestellung in kg."""
    total = 0.0
    for item in items:
        total += item["weight_kg"] * item["quantity"]
    return round(total, 2)


# ------------------------------------------------------------
# Anlegen
# ------------------------------------------------------------


def create_order(
    conn: sqlite3.Connection,
    cart_id: int,
    customer: dict,
    address: dict,
    clock: Callable[[], datetime] = datetime.now,
) -> dict:
    """Legt aus einem Warenkorb eine Bestellung an.

    Reserviert den Bestand. Ein Warenkorb kann nur einmal
    bestellt werden.
    """
    customer = validate_customer(customer)
    address = validate_address(address)
    used = conn.execute(
        "SELECT id FROM orders WHERE cart_id = ?", (cart_id,)
    ).fetchone()
    if used is not None:
        raise InvalidState(
            f"Warenkorb {cart_id} wurde schon bestellt "
            f"(Bestellung {used['id']})"
        )
    summary = cart.cart_summary(
        conn, cart_id, address["country"]
    )
    if not summary["lines"]:
        raise ValidationFailed("Warenkorb ist leer")
    lines = [
        (li["sku"], li["quantity"]) for li in summary["lines"]
    ]
    inventory.reserve(conn, lines)
    cur = conn.execute(
        "INSERT INTO orders (cart_id, customer_name, "
        "customer_mail, customer_type, ship_name, ship_street, "
        "ship_postal, ship_city, ship_country, status, "
        "subtotal, discount, shipping, total, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            cart_id,
            customer["name"],
            customer["email"],
            customer["type"],
            address["name"],
            address["street"],
            address["postal_code"],
            address["city"],
            address["country"],
            STATUS_NEW,
            summary["subtotal"],
            summary["discount"],
            summary["shipping"],
            summary["total"],
            clock().strftime(DATE_FORMAT),
        ),
    )
    order_id = cur.lastrowid
    conn.executemany(
        "INSERT INTO order_items (order_id, sku, name, "
        "quantity, unit_price, weight_kg) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                order_id,
                li["sku"],
                li["name"],
                li["quantity"],
                li["unit_price"],
                li["weight_kg"],
            )
            for li in summary["lines"]
        ],
    )
    conn.commit()
    return get_order(conn, order_id)


# ------------------------------------------------------------
# Status
# ------------------------------------------------------------


def set_status(
    conn: sqlite3.Connection,
    order_id: int,
    new_status: str,
    clock: Callable[[], datetime] = datetime.now,
) -> dict:
    """Wechselt den Status und bucht den Bestand passend."""
    order = get_order(conn, order_id)
    old_status = order["status"]
    if new_status not in STATUSES:
        raise ValidationFailed(
            f"Status {new_status!r} unbekannt"
        )
    if new_status not in TRANSITIONS[old_status]:
        raise InvalidState(
            f"Wechsel von {old_status} nach {new_status} "
            "ist nicht erlaubt"
        )
    lines = _lines(order["items"])
    if new_status == "zahlung_fehlgeschlagen":
        inventory.release(conn, lines)
    if new_status == STATUS_SHIPPED:
        if order["tracking_number"] is None:
            raise InvalidState(
                "Versand ohne Label nicht möglich"
            )
        inventory.ship(conn, lines)
    conn.execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (new_status, order_id),
    )
    conn.execute(
        "INSERT INTO status_log (order_id, old_status, "
        "new_status, changed_at) VALUES (?, ?, ?, ?)",
        (
            order_id,
            old_status,
            new_status,
            clock().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    return get_order(conn, order_id)


def status_history(
    conn: sqlite3.Connection, order_id: int
) -> list[dict]:
    _order_row(conn, order_id)
    rows = conn.execute(
        "SELECT old_status, new_status, changed_at "
        "FROM status_log WHERE order_id = ? ORDER BY id",
        (order_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def create_label(
    conn: sqlite3.Connection,
    order_id: int,
    clock: Callable[[], datetime] = datetime.now,
) -> dict:
    order = get_order(conn, order_id)
    return labels.create_label(conn, order, clock)


# ------------------------------------------------------------
# Texte für Kunde und Kundenservice
# ------------------------------------------------------------


def confirmation_text(order: dict) -> str:
    """Text der Bestellbestätigung per E-Mail."""
    lines = [
        f"Vielen Dank für Ihre Bestellung bei {SHOP_NAME}!",
        "",
        f"Bestellnummer: {order['id']}",
        f"Bestellt am:   {order['created_at']}",
        "",
    ]
    for item in order["items"]:
        lines.append(
            f"{item['quantity']} x {item['name']} "
            f"je {cart.format_eur(item['unit_price'])}"
        )
    lines.append("")
    if order["customer_type"] == "business":
        net = order["total"] / (1 + VAT_PERCENT / 100)
        lines.append(f"Gesamtbetrag: {cart.format_eur(net)}")
    else:
        lines.append(
            f"Gesamtbetrag: {cart.format_eur(order['total'])} "
            f"(inkl. {VAT_PERCENT} % MwSt.)"
        )
    if order["shipping"] == 0:
        lines.append("Der Versand ist für Sie kostenlos.")
    if order["bulky"]:
        lines.append(
            "Hinweis: Ihre Sendung wird als Sperrgut "
            "zugestellt. Das kann zwei Tage länger dauern."
        )
    lines += [
        "",
        "Lieferadresse:",
        order["ship_name"],
        order["ship_street"],
        f"{order['ship_postal']} {order['ship_city']}",
    ]
    return "\n".join(lines)


def service_summary(order: dict) -> str:
    """Einzeiler für die Kundenservice-Oberfläche."""
    tracking = order["tracking_number"] or "kein Label"
    return (
        f"#{order['id']} {order['customer_name']} | "
        f"{order['status']} | "
        f"{cart.format_eur(order['total'])} | {tracking}"
    )


# ------------------------------------------------------------
# Export für die Buchhaltung
# ------------------------------------------------------------

EXPORT_FIELDS = (
    "id",
    "created_at",
    "customer_name",
    "customer_type",
    "status",
    "subtotal",
    "discount",
    "shipping",
    "total",
)


def export_csv(conn: sqlite3.Connection) -> str:
    """Alle Bestellungen als CSV (Semikolon, Dezimalkomma)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(EXPORT_FIELDS)
    rows = conn.execute(
        "SELECT * FROM orders ORDER BY id"
    ).fetchall()
    for row in rows:
        values = []
        for field in EXPORT_FIELDS:
            value = row[field]
            if isinstance(value, float):
                value = f"{value:.2f}".replace(".", ",")
            values.append(value)
        writer.writerow(values)
    return buffer.getvalue()


def revenue_by_status(conn: sqlite3.Connection) -> dict:
    """Umsatzsumme je Status (für das Monatsgespräch)."""
    rows = conn.execute(
        "SELECT status, COUNT(*) AS n, SUM(total) AS revenue "
        "FROM orders GROUP BY status"
    ).fetchall()
    return {
        r["status"]: {
            "orders": r["n"],
            "revenue": round(r["revenue"] or 0.0, 2),
        }
        for r in rows
    }
