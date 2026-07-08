"use client";

export default function ProductTable({ products }) {
  if (!products?.length) {
    return <p style={{ color: "var(--muted)" }}>Aucun produit. Demande à l'agent d'en ajouter !</p>;
  }
  return (
    <table>
      <thead>
        <tr>
          <th>Produit</th>
          <th>Prix</th>
          <th>Stock</th>
        </tr>
      </thead>
      <tbody>
        {products.map((p) => (
          <tr key={p.id}>
            <td>{p.name}</td>
            <td>{Math.round(p.price).toLocaleString("fr-FR")} FCFA</td>
            <td className={p.stock <= 5 ? "low" : ""}>{p.stock}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
