"""Données de démonstration : python seed.py"""
from app.db import init_db
from app.services import inventory, sales

DEMO_PRODUCTS = [
    ("Riz 25kg", 18000, 12),
    ("Huile 5L", 7500, 8),
    ("Savon Citec", 600, 40),
    ("Sucre 1kg", 900, 25),
    ("Lait en poudre 400g", 2800, 3),
]

DEMO_SALES = [
    ("Riz 25kg", 1, "orange_money", "OM240701.1234"),
    ("Savon Citec", 5, "cash", None),
    ("Huile 5L", 2, "moov_money", "MM-889201"),
    ("Sucre 1kg", 3, "cash", None),
]


def main() -> None:
    init_db()
    for name, price, stock in DEMO_PRODUCTS:
        try:
            inventory.add_product(name, price, stock)
            print(f"+ produit : {name}")
        except ValueError:
            print(f"= produit déjà présent : {name}")
    for product_name, qty, method, ref in DEMO_SALES:
        try:
            sale = sales.record_sale(product_name, qty, method, ref)
            print(f"+ vente : {qty} × {product_name} = {sale['total']} FCFA")
        except ValueError as exc:
            print(f"! vente ignorée : {exc}")
    print("\nSeed terminé. Lance : uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
