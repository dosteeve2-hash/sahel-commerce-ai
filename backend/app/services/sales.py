"""Service ventes : enregistrement et statistiques."""
from ..db import get_conn
from . import inventory


def record_sale(
    product_name: str,
    quantity: int,
    payment_method: str = "cash",
    momo_ref: str | None = None,
) -> dict:
    product = inventory.get_product_by_name(product_name)
    if not product:
        raise ValueError(f"Produit introuvable : « {product_name} ».")
    inventory.adjust_stock(product_name, -quantity)  # lève si stock insuffisant
    total = round(product["price"] * quantity, 2)
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO sales (product_id, quantity, total, payment_method, momo_ref)"
            " VALUES (?, ?, ?, ?, ?)",
            (product["id"], quantity, total, payment_method, momo_ref),
        )
        row = conn.execute(
            "SELECT s.*, p.name AS product_name FROM sales s"
            " JOIN products p ON p.id = s.product_id WHERE s.id = ?",
            (cur.lastrowid,),
        ).fetchone()
    return dict(row)


def list_sales(limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT s.*, p.name AS product_name FROM sales s"
            " JOIN products p ON p.id = s.product_id"
            " ORDER BY s.created_at DESC, s.id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def sales_summary(days: int = 7) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count, COALESCE(SUM(total), 0) AS revenue FROM sales"
            " WHERE created_at >= datetime('now', ?)",
            (f"-{days} days",),
        ).fetchone()
        by_method = conn.execute(
            "SELECT payment_method, COUNT(*) AS count, COALESCE(SUM(total), 0) AS revenue"
            " FROM sales WHERE created_at >= datetime('now', ?) GROUP BY payment_method",
            (f"-{days} days",),
        ).fetchall()
        top = conn.execute(
            "SELECT p.name, SUM(s.quantity) AS sold, SUM(s.total) AS revenue"
            " FROM sales s JOIN products p ON p.id = s.product_id"
            " WHERE s.created_at >= datetime('now', ?)"
            " GROUP BY p.name ORDER BY revenue DESC LIMIT 5",
            (f"-{days} days",),
        ).fetchall()
    return {
        "days": days,
        "sales_count": row["count"],
        "revenue": row["revenue"],
        "by_payment_method": [dict(r) for r in by_method],
        "top_products": [dict(r) for r in top],
    }
