// Mode démo navigateur : réplique l'API backend en local (localStorage).
// Permet au site déployé d'être 100 % utilisable sans backend — les données
// restent sur l'appareil. Le vrai agent LLM nécessite le backend.

const KEY = "sahel-demo-v1";

const SEED = {
  products: [
    { id: 1, name: "Riz 25kg", price: 18000, stock: 11, created_at: iso(-6) },
    { id: 2, name: "Huile 5L", price: 7500, stock: 6, created_at: iso(-6) },
    { id: 3, name: "Savon Citec", price: 600, stock: 35, created_at: iso(-6) },
    { id: 4, name: "Sucre 1kg", price: 900, stock: 22, created_at: iso(-6) },
    { id: 5, name: "Lait en poudre 400g", price: 2800, stock: 3, created_at: iso(-6) },
  ],
  sales: [
    sale(1, 1, "Riz 25kg", 1, 18000, "orange_money", "OM240701.1234", -2),
    sale(2, 3, "Savon Citec", 5, 3000, "cash", null, -2),
    sale(3, 2, "Huile 5L", 2, 15000, "moov_money", "MM-889201", -1),
    sale(4, 4, "Sucre 1kg", 3, 2700, "cash", null, 0),
  ],
  momoTx: [],
};

function iso(daysAgo) {
  const d = new Date();
  d.setDate(d.getDate() + daysAgo);
  return d.toISOString().replace("T", " ").slice(0, 19);
}

function sale(id, product_id, product_name, quantity, total, payment_method, momo_ref, daysAgo) {
  return { id, product_id, product_name, quantity, total, payment_method, momo_ref, created_at: iso(daysAgo) };
}

function load() {
  if (typeof window === "undefined") return structuredClone(SEED);
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  const state = structuredClone(SEED);
  save(state);
  return state;
}

function save(state) {
  if (typeof window !== "undefined") {
    try {
      localStorage.setItem(KEY, JSON.stringify(state));
    } catch {}
  }
}

function fmtFCFA(n) {
  return `${Math.round(n).toLocaleString("fr-FR")} FCFA`;
}

// ---------------------------------------------------------------------------
// API équivalente au backend
// ---------------------------------------------------------------------------

export function products() {
  return [...load().products].sort((a, b) => a.name.localeCompare(b.name));
}

export function sales(limit = 50) {
  return [...load().sales].sort((a, b) => (a.created_at < b.created_at ? 1 : -1)).slice(0, limit);
}

export function salesSummary(days = 7) {
  const state = load();
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  const recent = state.sales.filter((s) => new Date(s.created_at) >= cutoff);
  const byMethod = {};
  for (const s of recent) {
    byMethod[s.payment_method] ??= { payment_method: s.payment_method, count: 0, revenue: 0 };
    byMethod[s.payment_method].count += 1;
    byMethod[s.payment_method].revenue += s.total;
  }
  const byProduct = {};
  for (const s of recent) {
    byProduct[s.product_name] ??= { name: s.product_name, sold: 0, revenue: 0 };
    byProduct[s.product_name].sold += s.quantity;
    byProduct[s.product_name].revenue += s.total;
  }
  return {
    days,
    sales_count: recent.length,
    revenue: recent.reduce((acc, s) => acc + s.total, 0),
    by_payment_method: Object.values(byMethod),
    top_products: Object.values(byProduct).sort((a, b) => b.revenue - a.revenue).slice(0, 5),
  };
}

function recordSale(state, productName, quantity, method) {
  const product = state.products.find((p) => p.name.toLowerCase() === productName.toLowerCase().trim());
  if (!product) throw new Error(`Produit introuvable : « ${productName} ».`);
  if (product.stock < quantity)
    throw new Error(`Stock insuffisant pour « ${product.name} » : ${product.stock} en stock.`);
  product.stock -= quantity;
  const s = {
    id: Math.max(0, ...state.sales.map((x) => x.id)) + 1,
    product_id: product.id,
    product_name: product.name,
    quantity,
    total: Math.round(product.price * quantity * 100) / 100,
    payment_method: method,
    momo_ref: null,
    created_at: iso(0),
  };
  state.sales.push(s);
  return s;
}

export function chat(message) {
  const state = load();
  const msg = message.toLowerCase();

  if (/\b(stock|produit|catalogue|inventaire)\b/.test(msg)) {
    const lines = state.products.map((p) => `- ${p.name} : ${p.stock} en stock à ${fmtFCFA(p.price)}`);
    return { reply: "Voici ton stock :\n" + lines.join("\n"), tools_used: ["list_products"], demo_mode: true };
  }

  const m = msg.match(/vend[us]?\s+(\d+)\s+(.+?)(?:\s+(?:en|par|via)\s+(cash|orange|moov)|$)/);
  if (m) {
    const method = { orange: "orange_money", moov: "moov_money" }[m[3]] || "cash";
    try {
      const s = recordSale(state, m[2], parseInt(m[1], 10), method);
      save(state);
      return {
        reply: `Vente enregistrée : ${s.quantity} × ${s.product_name} = ${fmtFCFA(s.total)} (${method.replace("_", " ")}).`,
        tools_used: ["record_sale"],
        demo_mode: true,
      };
    } catch (err) {
      return { reply: err.message, tools_used: ["record_sale"], demo_mode: true };
    }
  }

  if (/\b(bilan|résumé|stat|chiffre|ca)\b/.test(msg)) {
    const s = salesSummary(7);
    return {
      reply: `Sur 7 jours : ${s.sales_count} ventes pour ${fmtFCFA(s.revenue)}.`,
      tools_used: ["get_sales_summary"],
      demo_mode: true,
    };
  }

  return {
    reply:
      "Mode démo navigateur (données locales). Essaie : « montre le stock », " +
      "« vends 2 Savon Citec en orange » ou « bilan de la semaine ». " +
      "Connecte le backend pour l'agent IA complet.",
    tools_used: [],
    demo_mode: true,
  };
}

// ---------------------------------------------------------------------------
// Réconciliation mobile money (port JS du parser Python)
// ---------------------------------------------------------------------------

const SMS_RE =
  /re[cç]ue?[\s:]+([\d\s.,]+?)\s*F\s*CFA[\s\S]*?de\s+([\w\s]+?)[.,][\s\S]*?[Rr]ef[\s.:]*([A-Za-z0-9.\-]+)/;

export function reconcile(smsText) {
  const state = load();
  const chunks = smsText.split(/\n+/).map((c) => c.trim()).filter(Boolean);
  let parsed = 0;

  for (const chunk of chunks) {
    const m = chunk.match(SMS_RE);
    if (!m) continue;
    parsed += 1;
    const ref = m[3].replace(/\.$/, "");
    if (state.momoTx.some((t) => t.ref === ref)) continue;
    const amount = parseFloat(m[1].replace(/[\s]/g, "").replace(",", "."));
    const lowered = chunk.toLowerCase();
    state.momoTx.push({
      ref,
      amount,
      sender: m[2].trim(),
      operator: lowered.includes("orange") ? "orange_money" : lowered.includes("moov") ? "moov_money" : null,
      created_at: iso(0),
      matched_sale_id: null,
    });
  }

  // 1. Par référence exacte, 2. par montant + même jour
  const usedSales = new Set(state.momoTx.map((t) => t.matched_sale_id).filter(Boolean));
  for (const tx of state.momoTx) {
    if (tx.matched_sale_id) continue;
    let match = state.sales.find((s) => s.momo_ref === tx.ref && !usedSales.has(s.id));
    if (!match) {
      match = state.sales.find(
        (s) =>
          s.payment_method !== "cash" &&
          Math.abs(s.total - tx.amount) < 0.01 &&
          s.created_at.slice(0, 10) === tx.created_at.slice(0, 10) &&
          !usedSales.has(s.id)
      );
    }
    if (match) {
      tx.matched_sale_id = match.id;
      usedSales.add(match.id);
    }
  }
  save(state);

  return {
    parsed,
    matched: state.momoTx.filter((t) => t.matched_sale_id).length,
    unmatched_transactions: state.momoTx
      .filter((t) => !t.matched_sale_id)
      .map(({ ref, amount, sender, operator }) => ({ ref, amount, sender, operator })),
    unmatched_sales: state.sales
      .filter((s) => s.payment_method !== "cash" && !usedSales.has(s.id))
      .map(({ id, product_name, total, payment_method, created_at }) => ({
        id,
        product_name,
        total,
        payment_method,
        created_at,
      })),
  };
}

export function reset() {
  if (typeof window !== "undefined") localStorage.removeItem(KEY);
}
