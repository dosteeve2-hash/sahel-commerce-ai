"""Accès SQLite. Une connexion par requête, schéma auto-créé au démarrage.

Le choix de SQLite est volontaire pour la v1 : zéro dépendance, démarrage
immédiat. La migration vers Supabase (Postgres) est prévue — voir
supabase/schema.sql à la racine du projet.
"""
import sqlite3
from contextlib import contextmanager

from .config import DATABASE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    price REAL NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    total REAL NOT NULL,
    payment_method TEXT NOT NULL DEFAULT 'cash', -- cash | orange_money | moov_money
    momo_ref TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS momo_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ref TEXT NOT NULL UNIQUE,
    amount REAL NOT NULL,
    sender TEXT,
    operator TEXT,               -- orange_money | moov_money
    raw_sms TEXT NOT NULL,
    matched_sale_id INTEGER REFERENCES sales(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def init_db() -> None:
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
