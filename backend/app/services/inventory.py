"""Service inventaire : produits et stock."""
from ..db import get_conn


def list_products() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def get_product_by_name(name: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE lower(name) = lower(?)", (name.strip(),)
        ).fetchone()
    return dict(row) if row else None


def add_product(name: str, price: float, stock: int = 0) -> dict:
    existing = get_product_by_name(name)
    if existing:
        raise ValueError(f"Le produit « {name} » existe déjà (id={existing['id']}).")
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
            (name.strip(), price, stock),
        )
        row = conn.execute("SELECT * FROM products WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def adjust_stock(name: str, delta: int) -> dict:
    product = get_product_by_name(name)
    if not product:
        raise ValueError(f"Produit introuvable : « {name} ».")
    new_stock = product["stock"] + delta
    if new_stock < 0:
        raise ValueError(
            f"Stock insuffisant pour « {name} » : {product['stock']} en stock, {-delta} demandés."
        )
    with get_conn() as conn:
        conn.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product["id"]))
    product["stock"] = new_stock
    return product


def low_stock(threshold: int = 5) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM products WHERE stock <= ? ORDER BY stock", (threshold,)
        ).fetchall()
    return [dict(r) for r in rows]
