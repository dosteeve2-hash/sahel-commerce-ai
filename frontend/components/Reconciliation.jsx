"use client";

import { useState } from "react";
import { api } from "../lib/api";

const EXAMPLE = `Vous avez recu 18000 FCFA de 70123456. Ref: OM240701.1234. Orange Money
Transfert recu: 15000 FCFA de OUEDRAOGO Ali. Ref MM-889201. Moov Money
Vous avez recu 5000 FCFA de 76001122. Ref: OM240705.9981. Orange Money`;

export default function Reconciliation({ onAction }) {
  const [text, setText] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    if (!text.trim() || loading) return;
    setLoading(true);
    setError("");
    try {
      const r = await api.reconcile(text);
      setReport(r);
      onAction?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <p style={{ color: "var(--muted)", marginBottom: 12, fontSize: "0.9rem" }}>
        Colle ici tes SMS Orange Money / Moov Money (un par ligne). L'outil les
        rapproche automatiquement de tes ventes enregistrées.
      </p>
      <textarea
        className="sms-input"
        rows={6}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={EXAMPLE}
        aria-label="SMS mobile money"
      />
      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
        <button onClick={run} disabled={loading || !text.trim()}>
          {loading ? "Analyse…" : "Réconcilier"}
        </button>
        <button className="secondary" onClick={() => setText(EXAMPLE)}>
          Utiliser l'exemple
        </button>
      </div>
      {error && <p className="error">{error}</p>}

      {report && (
        <div style={{ marginTop: 18 }}>
          <div className="stats" style={{ marginBottom: 14 }}>
            <div className="stat">
              <div className="label">SMS analysés</div>
              <div className="value">{report.parsed}</div>
            </div>
            <div className="stat">
              <div className="label">Rapprochés</div>
              <div className="value" style={{ color: "var(--green)" }}>
                {report.matched}
              </div>
            </div>
            <div className="stat">
              <div className="label">Anomalies</div>
              <div
                className="value"
                style={{
                  color: report.unmatched_transactions.length ? "var(--red)" : "var(--green)",
                }}
              >
                {report.unmatched_transactions.length + report.unmatched_sales.length}
              </div>
            </div>
          </div>

          {report.unmatched_transactions.length > 0 && (
            <>
              <h3 className="sub">⚠️ Paiements reçus sans vente correspondante</h3>
              <table>
                <thead>
                  <tr>
                    <th>Réf</th>
                    <th>Montant</th>
                    <th>Expéditeur</th>
                    <th>Opérateur</th>
                  </tr>
                </thead>
                <tbody>
                  {report.unmatched_transactions.map((t) => (
                    <tr key={t.ref}>
                      <td>{t.ref}</td>
                      <td>{Math.round(t.amount).toLocaleString("fr-FR")} FCFA</td>
                      <td>{t.sender}</td>
                      <td>{t.operator?.replace("_", " ") || "?"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {report.unmatched_sales.length > 0 && (
            <>
              <h3 className="sub">⚠️ Ventes momo sans paiement retrouvé</h3>
              <table>
                <thead>
                  <tr>
                    <th>Produit</th>
                    <th>Total</th>
                    <th>Paiement</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {report.unmatched_sales.map((s) => (
                    <tr key={s.id}>
                      <td>{s.product_name}</td>
                      <td>{Math.round(s.total).toLocaleString("fr-FR")} FCFA</td>
                      <td>{s.payment_method.replace("_", " ")}</td>
                      <td>{s.created_at?.slice(0, 16)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {!report.unmatched_transactions.length && !report.unmatched_sales.length && (
            <p style={{ color: "var(--green)" }}>
              ✅ Tout est rapproché — ta caisse mobile money est cohérente.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
