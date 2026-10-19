"""SQLite-Speicher des bestellservice (nur Standardbibliothek).

Jede App-Instanz bekommt standardmäßig eine eigene
In-Memory-Datenbank. Das hält die Tests unabhängig voneinander.
"""

import sqlite3

SCHEMA = """
CREATE TABLE articles (
    sku         TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL,
    price       REAL NOT NULL,
    weight_kg   REAL NOT NULL,
    bulk_from   INTEGER,
    bulk_price  REAL,
    active      INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE stock (
    sku         TEXT PRIMARY KEY REFERENCES articles(sku),
    on_hand     INTEGER NOT NULL,
    reserved    INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE coupons (
    code        TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,
    value       REAL NOT NULL,
    min_total   REAL NOT NULL DEFAULT 0
);
CREATE TABLE carts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    coupon_code TEXT,
    created_at  TEXT NOT NULL
);
CREATE TABLE cart_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_id     INTEGER NOT NULL REFERENCES carts(id),
    sku         TEXT NOT NULL REFERENCES articles(sku),
    quantity    INTEGER NOT NULL
);
CREATE TABLE orders (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_id       INTEGER NOT NULL,
    customer_name TEXT NOT NULL,
    customer_mail TEXT NOT NULL,
    customer_type TEXT NOT NULL,
    ship_name     TEXT NOT NULL,
    ship_street   TEXT NOT NULL,
    ship_postal   TEXT NOT NULL,
    ship_city     TEXT NOT NULL,
    ship_country  TEXT NOT NULL,
    status        TEXT NOT NULL,
    subtotal      REAL NOT NULL,
    discount      REAL NOT NULL,
    shipping      REAL NOT NULL,
    total         REAL NOT NULL,
    created_at    TEXT NOT NULL
);
CREATE TABLE order_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER NOT NULL REFERENCES orders(id),
    sku         TEXT NOT NULL,
    name        TEXT NOT NULL,
    quantity    INTEGER NOT NULL,
    unit_price  REAL NOT NULL,
    weight_kg   REAL NOT NULL
);
CREATE TABLE labels (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL REFERENCES orders(id),
    tracking_number TEXT NOT NULL,
    tariff_code     TEXT NOT NULL,
    weight_kg       REAL NOT NULL,
    text            TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE TABLE status_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER NOT NULL REFERENCES orders(id),
    old_status  TEXT NOT NULL,
    new_status  TEXT NOT NULL,
    changed_at  TEXT NOT NULL
);
"""

# sku, name, category, price, weight_kg, bulk_from, bulk_price
ARTICLES = [
    (
        "AKS-18",
        "Akkuschrauber 18 V",
        "Elektrowerkzeug",
        89.90,
        1.6,
        None,
        None,
    ),
    (
        "SGS-K",
        "Stichsäge mit Pendelhub",
        "Elektrowerkzeug",
        119.00,
        2.4,
        None,
        None,
    ),
    (
        "KS-254",
        "Kappsäge 254 mm",
        "Elektrowerkzeug",
        279.00,
        17.5,
        None,
        None,
    ),
    (
        "BIT-32",
        "Bitsatz 32-teilig",
        "Zubehör",
        12.50,
        0.3,
        None,
        None,
    ),
    (
        "SP-120",
        "Schleifpapier K120, 50 Blatt",
        "Zubehör",
        13.70,
        0.4,
        None,
        None,
    ),
    (
        "HL-750",
        "Holzleim 750 g",
        "Verbrauch",
        7.80,
        0.8,
        None,
        None,
    ),
    (
        "ZB-01",
        "Zimmermannsbleistift",
        "Verbrauch",
        1.10,
        0.02,
        None,
        None,
    ),
    (
        "WW-120",
        "Wasserwaage 120 cm",
        "Messen",
        50.00,
        1.2,
        None,
        None,
    ),
    ("ZS-2", "Zollstock 2 m", "Messen", 6.95, 0.3, None, None),
    (
        "SCH-440",
        "Spanplattenschrauben 4x40, 500 Stück",
        "Befestigung",
        9.95,
        1.1,
        10,
        8.95,
    ),
    (
        "DUE-6",
        "Dübel 6 mm, 100 Stück",
        "Befestigung",
        3.49,
        0.2,
        10,
        2.99,
    ),
    (
        "HS-550",
        "Handsäge 550 mm",
        "Handwerkzeug",
        24.90,
        0.7,
        None,
        None,
    ),
    (
        "HAM-300",
        "Schlosserhammer 300 g",
        "Handwerkzeug",
        14.95,
        0.5,
        None,
        None,
    ),
    (
        "AH-10",
        "Arbeitshandschuhe Gr. 10",
        "Arbeitsschutz",
        4.95,
        0.1,
        10,
        4.25,
    ),
    (
        "SK-24",
        "Sortimentskasten 24 Fächer",
        "Lagern",
        19.99,
        2.1,
        None,
        None,
    ),
    (
        "AL-3",
        "Aluleiter 3-teilig",
        "Leitern",
        149.00,
        14.5,
        None,
        None,
    ),
    (
        "ZE-25",
        "Zement 25 kg",
        "Baustoffe",
        8.49,
        25.0,
        None,
        None,
    ),
    (
        "FK-20",
        "Fliesenkleber 20 kg",
        "Baustoffe",
        16.90,
        20.0,
        None,
        None,
    ),
    (
        "SR-180",
        "Schwerlastregal 180 x 90 cm",
        "Lagern",
        129.00,
        33.5,
        None,
        None,
    ),
    (
        "WB-200",
        "Werkbank Buche 200 cm",
        "Werkstatt",
        389.00,
        38.0,
        None,
        None,
    ),
]

STOCK = {
    "AKS-18": 40,
    "SGS-K": 12,
    "KS-254": 3,
    "BIT-32": 120,
    "SP-120": 200,
    "HL-750": 80,
    "ZB-01": 500,
    "WW-120": 25,
    "ZS-2": 90,
    "SCH-440": 300,
    "DUE-6": 400,
    "HS-550": 35,
    "HAM-300": 60,
    "AH-10": 250,
    "SK-24": 30,
    "AL-3": 2,
    "ZE-25": 60,
    "FK-20": 45,
    "SR-180": 8,
    "WB-200": 4,
}

COUPONS = [
    ("NORDLICHT10", "percent", 10.0, 0.0),
    ("WERKBANK20", "amount", 20.0, 200.0),
]


def connect(path: str = ":memory:") -> sqlite3.Connection:
    """Öffnet die Datenbank, legt bei Bedarf das Schema an."""
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    exists = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='articles'"
    ).fetchone()
    if not exists:
        conn.executescript(SCHEMA)
        seed(conn)
    return conn


def seed(conn: sqlite3.Connection) -> None:
    """Füllt Katalog, Bestand und Gutscheine (Beispieldaten)."""
    conn.executemany(
        "INSERT INTO articles (sku, name, category, price, "
        "weight_kg, bulk_from, bulk_price) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ARTICLES,
    )
    conn.executemany(
        "INSERT INTO stock (sku, on_hand) VALUES (?, ?)",
        STOCK.items(),
    )
    conn.executemany(
        "INSERT INTO coupons VALUES (?, ?, ?, ?)", COUPONS
    )
    # Bestellnummern beginnen wie im Altsystem bei 10230.
    conn.execute(
        "INSERT INTO sqlite_sequence (name, seq) "
        "VALUES ('orders', 10229)"
    )
    conn.commit()
