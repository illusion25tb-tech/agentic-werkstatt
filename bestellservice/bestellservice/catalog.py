"""Artikelkatalog: Lesen, Suchen, Staffelpreise."""

import sqlite3
from dataclasses import dataclass

from .errors import NotFound


@dataclass(frozen=True)
class Article:
    sku: str
    name: str
    category: str
    price: float
    weight_kg: float
    bulk_from: int | None = None
    bulk_price: float | None = None
    active: bool = True

    def to_dict(self) -> dict:
        return {
            "sku": self.sku,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "weight_kg": self.weight_kg,
            "bulk_from": self.bulk_from,
            "bulk_price": self.bulk_price,
        }


def _from_row(row: sqlite3.Row) -> Article:
    return Article(
        sku=row["sku"],
        name=row["name"],
        category=row["category"],
        price=row["price"],
        weight_kg=row["weight_kg"],
        bulk_from=row["bulk_from"],
        bulk_price=row["bulk_price"],
        active=bool(row["active"]),
    )


def get_article(conn: sqlite3.Connection, sku: str) -> Article:
    row = conn.execute(
        "SELECT * FROM articles WHERE sku = ?", (sku,)
    ).fetchone()
    if row is None:
        raise NotFound(f"Artikel {sku} existiert nicht")
    return _from_row(row)


def list_articles(
    conn: sqlite3.Connection, category: str | None = None
) -> list[Article]:
    sql = "SELECT * FROM articles WHERE active = 1"
    args: tuple = ()
    if category:
        sql += " AND category = ?"
        args = (category,)
    rows = conn.execute(sql + " ORDER BY sku", args).fetchall()
    return [_from_row(r) for r in rows]


def categories(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT category FROM articles "
        "WHERE active = 1 ORDER BY category"
    ).fetchall()
    return [r["category"] for r in rows]


def search(
    conn: sqlite3.Connection, query: str
) -> list[Article]:
    """Sucht Artikel nach Name oder Artikelnummer.

    Groß- und Kleinschreibung spielt keine Rolle.
    """
    q = query.strip().lower()
    if not q:
        return []
    hits = []
    for article in list_articles(conn):
        name = article.name.lower()
        sku = article.sku.lower()
        if name.startswith(q) or sku.startswith(q):
            hits.append(article)
    return hits


def unit_price(article: Article, quantity: int) -> float:
    """Stückpreis unter Berücksichtigung der Staffel.

    Artikel mit `bulk_from` kosten ab dieser Menge den
    Staffelpreis `bulk_price`.
    """
    if article.bulk_from and article.bulk_price is not None:
        if quantity > article.bulk_from:
            return article.bulk_price
    return article.price


def deactivate(conn: sqlite3.Connection, sku: str) -> None:
    get_article(conn, sku)
    conn.execute(
        "UPDATE articles SET active = 0 WHERE sku = ?", (sku,)
    )
    conn.commit()
