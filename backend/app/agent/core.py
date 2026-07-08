"""Boucle agentique : LLM + tool-calling, avec mode démo sans clé API.

Architecture :
- run_agent() choisit entre le vrai agent (Claude, boucle tool-use)
  et le mode démo rule-based (regex d'intentions) si aucune clé n'est configurée.
- Le mode démo permet de tester toute la chaîne (API, services, front)
  sans dépendance externe — utile en entretien ou hors connexion.
"""
import re

from anthropic import Anthropic

from ..config import AGENT_MODEL, ANTHROPIC_API_KEY
from ..services import inventory, sales
from .prompts import SYSTEM_PROMPT
from .tools import TOOL_SCHEMAS, execute_tool

MAX_TURNS = 8  # garde-fou contre les boucles infinies


def run_agent(message: str) -> dict:
    if not ANTHROPIC_API_KEY:
        return _run_demo(message)
    return _run_llm(message)


def _run_llm(message: str) -> dict:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    messages = [{"role": "user", "content": message}]
    tools_used: list[str] = []

    for _ in range(MAX_TURNS):
        response = client.messages.create(
            model=AGENT_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )
        if response.stop_reason != "tool_use":
            text = "".join(b.text for b in response.content if b.type == "text")
            return {"reply": text.strip(), "tools_used": tools_used, "demo_mode": False}

        # Exécuter chaque tool_use demandé, renvoyer les résultats au modèle
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tools_used.append(block.name)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": execute_tool(block.name, block.input),
                    }
                )
        messages.append({"role": "user", "content": tool_results})

    return {
        "reply": "Je n'ai pas réussi à terminer cette demande, peux-tu reformuler ?",
        "tools_used": tools_used,
        "demo_mode": False,
    }


# ---------------------------------------------------------------------------
# Mode démo (sans clé API) : détection d'intentions par regex
# ---------------------------------------------------------------------------

def _fmt(amount: float) -> str:
    return f"{amount:,.0f}".replace(",", " ") + " FCFA"


def _run_demo(message: str) -> dict:
    msg = message.lower()

    if re.search(r"\b(stock|produit|catalogue|inventaire)\b", msg):
        products = inventory.list_products()
        if not products:
            reply = "Le catalogue est vide. Dis-moi par exemple : « ajoute Riz 25kg à 18000 FCFA, 10 en stock »."
        else:
            lines = [f"- {p['name']} : {p['stock']} en stock à {_fmt(p['price'])}" for p in products]
            reply = "Voici ton stock :\n" + "\n".join(lines)
        return {"reply": reply, "tools_used": ["list_products"], "demo_mode": True}

    m = re.search(r"vend[us]?\s+(\d+)\s+(.+?)(?:\s+(?:en|par|via)\s+(cash|orange|moov)|$)", msg)
    if m:
        quantity, name = int(m.group(1)), m.group(2).strip()
        method = {"orange": "orange_money", "moov": "moov_money"}.get(m.group(3) or "cash", "cash")
        try:
            sale = sales.record_sale(name, quantity, method)
            reply = (
                f"Vente enregistrée : {quantity} × {sale['product_name']}"
                f" = {_fmt(sale['total'])} ({method.replace('_', ' ')})."
            )
        except ValueError as exc:
            reply = str(exc)
        return {"reply": reply, "tools_used": ["record_sale"], "demo_mode": True}

    if re.search(r"\b(bilan|résumé|stat|chiffre|ca)\b", msg):
        s = sales.sales_summary(7)
        reply = (
            f"Sur 7 jours : {s['sales_count']} ventes pour {_fmt(s['revenue'])}."
        )
        return {"reply": reply, "tools_used": ["get_sales_summary"], "demo_mode": True}

    return {
        "reply": (
            "Mode démo (aucune clé API configurée). Essaie : « montre le stock », "
            "« vends 2 Savon en orange » ou « bilan de la semaine ». "
            "Configure ANTHROPIC_API_KEY pour l'agent complet."
        ),
        "tools_used": [],
        "demo_mode": True,
    }
