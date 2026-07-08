"use client";

const METHOD_LABELS = {
  cash: "Cash",
  orange_money: "Orange Money",
  moov_money: "Moov Money",
};

export default function SalesTable({ sales }) {
  if (!sales?.length) {
    return <p style={{ color: "var(--muted)" }}>Aucune vente enregistrée pour l'instant.</p>;
  }
  return (
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Produit</th>
          <th>Qté</th>
          <th>Total</th>
          <th>Paiement</th>
          <th>Réf momo</th>
        </tr>
      </thead>
      <tbody>
        {sales.map((s) => (
          <tr key={s.id}>
            <td>{s.created_at?.slice(0, 16).replace("T", " ")}</td>
            <td>{s.product_name}</td>
            <td>{s.quantity}</td>
            <td>{Math.round(s.total).toLocaleString("fr-FR")} FCFA</td>
            <td>
              <span className={`badge ${s.payment_method}`}>
                {METHOD_LABELS[s.payment_method] || s.payment_method}
              </span>
            </td>
            <td style={{ color: "var(--muted)" }}>{s.momo_ref || "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
