"""Réconciliation mobile money (Orange Money / Moov Money).

Le commerçant colle ses SMS de confirmation ; on les parse par regex,
on les stocke, puis on les rapproche des ventes enregistrées :
1. par référence exacte (momo_ref saisi à la vente),
2. sinon par montant identique le même jour.
"""
import re

from ..db import get_conn

# Exemples de SMS supportés :
#  "Vous avez recu 5000 FCFA de 70123456. Ref: OM240701.1234. Orange Money"
#  "Transfert recu: 2500 FCFA de OUEDRAOGO Ali. Ref MM-889201. Moov Money"
SMS_PATTERNS = [
    re.compile(
        r"re[cç]u[e]?[\s:]+(?P<amount>[\d\s.,]+?)\s*F\s*CFA.*?"
        r"de\s+(?P<sender>[\w\s]+?)[.,].*?"
        r"[Rr]ef[\s.:]*(?P<ref>[A-Za-z0-9.\-]+)",
        re.DOTALL,
    ),
]


def _detect_operator(sms: str) -> str | None:
    lowered = sms.lower()
    if "orange" in lowered:
        return "orange_money"
    if "moov" in lowered:
        return "moov_money"
    return None


def parse_sms_block(sms_text: str) -> list[dict]:
    """Découpe un bloc de SMS collés et extrait montant / expéditeur / référence."""
    parsed: list[dict] = []
    chunks = [c.strip() for c in re.split(r"\n{1,}", sms_text) if c.strip()]
    for chunk in chunks:
        for pattern in SMS_PATTERNS:
            m = pattern.search(chunk)
            if m:
                amount = float(re.sub(r"[\s.,](?=\d{3}\b)|[\s]", "", m.group("amount")).replace(",", "."))
                parsed.append(
                    {
                        "ref": m.group("ref").rstrip("."),
                        "amount": amount,
                        "sender": m.group("sender").strip(),
                        "operator": _detect_operator(chunk),
                        "raw_sms": chunk,
                    }
                )
                break
    return parsed


def _store_transactions(transactions: list[dict]) -> None:
    with get_conn() as conn:
        for t in transactions:
            conn.execute(
                "INSERT OR IGNORE INTO momo_transactions (ref, amount, sender, operator, raw_sms)"
                " VALUES (?, ?, ?, ?, ?)",
                (t["ref"], t["amount"], t["sender"], t["operator"], t["raw_sms"]),
            )


def reconcile(sms_text: str) -> dict:
    """Parse les SMS, stocke les transactions, puis rapproche avec les ventes momo."""
    transactions = parse_sms_block(sms_text)
    _store_transactions(transactions)

    matched = 0
    with get_conn() as conn:
        # 1. Rapprochement par référence exacte
        conn.execute(
            """
            UPDATE momo_transactions SET matched_sale_id = (
                SELECT s.id FROM sales s
                WHERE s.momo_ref = momo_transactions.ref
                LIMIT 1
            )
            WHERE matched_sale_id IS NULL
            """
        )
        # 2. Rapprochement par montant + même jour
        conn.execute(
            """
            UPDATE momo_transactions SET matched_sale_id = (
                SELECT s.id FROM sales s
                WHERE s.payment_method != 'cash'
                  AND abs(s.total - momo_transactions.amount) < 0.01
                  AND date(s.created_at) = date(momo_transactions.created_at)
                  AND s.id NOT IN (
                      SELECT matched_sale_id FROM momo_transactions
                      WHERE matched_sale_id IS NOT NULL
                  )
                LIMIT 1
            )
            WHERE matched_sale_id IS NULL
            """
        )
        matched = conn.execute(
            "SELECT COUNT(*) AS c FROM momo_transactions WHERE matched_sale_id IS NOT NULL"
        ).fetchone()["c"]
        unmatched_tx = conn.execute(
            "SELECT ref, amount, sender, operator FROM momo_transactions"
            " WHERE matched_sale_id IS NULL"
        ).fetchall()
        unmatched_sales = conn.execute(
            """
            SELECT s.id, p.name AS product_name, s.total, s.payment_method, s.created_at
            FROM sales s JOIN products p ON p.id = s.product_id
            WHERE s.payment_method != 'cash'
              AND s.id NOT IN (
                  SELECT matched_sale_id FROM momo_transactions
                  WHERE matched_sale_id IS NOT NULL
              )
            """
        ).fetchall()

    return {
        "parsed": len(transactions),
        "matched": matched,
        "unmatched_transactions": [dict(r) for r in unmatched_tx],
        "unmatched_sales": [dict(r) for r in unmatched_sales],
    }
