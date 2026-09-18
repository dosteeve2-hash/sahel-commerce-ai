"use client";

import { useCallback, useEffect, useState } from "react";
import Chat from "../components/Chat";
import ProductTable from "../components/ProductTable";
import Reconciliation from "../components/Reconciliation";
import SalesTable from "../components/SalesTable";
import StatsCards from "../components/StatsCards";
import { api, isDemoMode } from "../lib/api";

const TABS = [
  { id: "assistant", label: "💬 Assistant" },
  { id: "ventes", label: "🧾 Ventes" },
  { id: "momo", label: "📱 Réconciliation" },
];

export default function Home() {
  const [tab, setTab] = useState("assistant");
  const [products, setProducts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [sales, setSales] = useState([]);
  const [demo, setDemo] = useState(false);

  const refresh = useCallback(async () => {
    const [p, s, list] = await Promise.all([
      api.products(),
      api.salesSummary(7),
      api.sales(30),
    ]);
    setProducts(p);
    setSummary(s);
    setSales(list);
    setDemo(isDemoMode());
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Le correctif de lib/reseau.js permet à l'application de REVENIR en ligne.
  // Encore faut-il que quelque chose le déclenche : `refresh` ne tournait qu'au
  // montage, si bien que la bannière restait affichée pour toute la session même
  // une fois le réseau rétabli.
  //
  // On écoute l'événement du système plutôt que d'interroger le réseau en
  // boucle : sur un forfait payé au mégaoctet, un sondage périodique se paie.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const auRetour = () => refresh();
    window.addEventListener("online", auRetour);
    return () => window.removeEventListener("online", auRetour);
  }, [refresh]);

  return (
    <main className="container">
      <div className="header">
        <h1>Sahel Commerce AI</h1>
        <span className="tag">agent IA · commerce · mobile money</span>
      </div>

      {demo && (
        <p className="banner" role="status">
          Hors ligne — les données restent sur cet appareil. La connexion au
          serveur est retentée automatiquement.
        </p>
      )}

      <StatsCards summary={summary} />

      <nav className="tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            className={`tab ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "assistant" && (
        <div className="grid">
          <section className="panel">
            <h2>Assistant</h2>
            <Chat onAction={refresh} />
          </section>
          <section className="panel">
            <h2>Stock</h2>
            <ProductTable products={products} />
          </section>
        </div>
      )}

      {tab === "ventes" && (
        <section className="panel">
          <h2>Historique des ventes</h2>
          <SalesTable sales={sales} />
        </section>
      )}

      {tab === "momo" && (
        <section className="panel">
          <h2>Réconciliation mobile money</h2>
          <Reconciliation onAction={refresh} />
        </section>
      )}
    </main>
  );
}
