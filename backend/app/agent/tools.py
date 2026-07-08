"""Définition des outils exposés à l'agent + exécution.

Chaque outil = un schéma (envoyé au LLM) + un handler (fonction Python).
"""
import json

from ..services import inventory, momo, sales

TOOL_SCHEMAS = [
    {
        "name": "list_products",
        "description": "Liste tous les produits avec prix et stock.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "add_product",
        "description": "Ajoute un nouveau produit au catalogue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nom du produit"},
                "price": {"type": "number", "description": "Prix unitaire en FCFA"},
                "stock": {"type": "integer", "description": "Quantité initiale en stock"},
            },
            "required": ["name", "price"],
        },
    },
    {
        "name": "adjust_stock",
        "description": "Ajoute (delta positif) ou retire (delta négatif) du stock d'un produit existant.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "delta": {"type": "integer", "description": "Variation de stock (ex: +10, -3)"},
            },
            "required": ["name", "delta"],
        },
    },
    {
        "name": "record_sale",
        "description": "Enregistre une vente : décrémente le stock et calcule le total.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "quantity": {"type": "integer"},
                "payment_method": {
                    "type": "string",
                    "enum": ["cash", "orange_money", "moov_money"],
                },
                "momo_ref": {
                    "type": "string",
                    "description": "Référence de la transaction mobile money, si connue",
                },
            },
            "required": ["product_name", "quantity"],
        },
    },
    {
        "name": "get_sales_summary",
        "description": "Statistiques de ventes sur N jours : CA, nombre de ventes, top produits, répartition par moyen de paiement.",
        "input_schema": {
            "type": "object",
            "properties": {"days": {"type": "integer", "description": "Période en jours (défaut 7)"}},
            "required": [],
        },
    },
    {
        "name": "get_low_stock",
        "description": "Liste les produits dont le stock est sous un seuil.",
        "input_schema": {
            "type": "object",
            "properties": {"threshold": {"type": "integer", "description": "Seuil (défaut 5)"}},
            "required": [],
        },
    },
    {
        "name": "reconcile_momo",
        "description": "Parse des SMS mobile money collés par le commerçant et les rapproche des ventes enregistrées.",
        "input_schema": {
            "type": "object",
            "properties": {"sms_text": {"type": "string", "description": "SMS bruts, collés tels quels"}},
            "required": ["sms_text"],
        },
    },
]

_HANDLERS = {
    "list_products": lambda args: inventory.list_products(),
    "add_product": lambda args: inventory.add_product(
        args["name"], args["price"], args.get("stock", 0)
    ),
    "adjust_stock": lambda args: inventory.adjust_stock(args["name"], args["delta"]),
    "record_sale": lambda args: sales.record_sale(
        args["product_name"],
        args["quantity"],
        args.get("payment_method", "cash"),
        args.get("momo_ref"),
    ),
    "get_sales_summary": lambda args: sales.sales_summary(args.get("days", 7)),
    "get_low_stock": lambda args: inventory.low_stock(args.get("threshold", 5)),
    "reconcile_momo": lambda args: momo.reconcile(args["sms_text"]),
}


def execute_tool(name: str, args: dict) -> str:
    """Exécute un outil et renvoie le résultat en JSON (ou l'erreur, lisible par le LLM)."""
    handler = _HANDLERS.get(name)
    if not handler:
        return json.dumps({"error": f"Outil inconnu : {name}"})
    try:
        result = handler(args or {})
        return json.dumps(result, ensure_ascii=False, default=str)
    except ValueError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)
