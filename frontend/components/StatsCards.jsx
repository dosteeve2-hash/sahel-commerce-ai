"use client";

function fmtFCFA(n) {
  return `${Math.round(n).toLocaleString("fr-FR")} FCFA`;
}

export default function StatsCards({ summary }) {
  if (!summary) return null;
  const momo = (summary.by_payment_method || [])
    .filter((m) => m.payment_method !== "cash")
    .reduce((acc, m) => acc + m.revenue, 0);

  return (
    <div className="stats">
      <div className="stat">
        <div className="label">Chiffre d'affaires ({summary.days} j)</div>
        <div className="value accent">{fmtFCFA(summary.revenue)}</div>
      </div>
      <div className="stat">
        <div className="label">Ventes ({summary.days} j)</div>
        <div className="value">{summary.sales_count}</div>
      </div>
      <div className="stat">
        <div className="label">Dont mobile money</div>
        <div className="value">{fmtFCFA(momo)}</div>
      </div>
    </div>
  );
}
