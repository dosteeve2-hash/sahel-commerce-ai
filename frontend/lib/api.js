// Client API avec bascule automatique : backend FastAPI si joignable,
// sinon mode démo navigateur (lib/demo.js, données locales).

import * as demo from "./demo";
import { creerEtatReseau } from "./reseau";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const reseau = creerEtatReseau();

// Le système sait avant nous que la connexion est revenue : on en profite pour
// retenter sans attendre la fin du délai.
if (typeof window !== "undefined") {
  window.addEventListener("online", () => reseau.connexionAnnoncee());
}

/** L'application lit-elle les données de l'appareil plutôt que le serveur ? */
export function isDemoMode() {
  return reseau.estLocal();
}

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    signal: AbortSignal.timeout(5000),
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(body.detail || `Erreur API (${res.status})`);
  }
  return res.json();
}

class ApiError extends Error {}

async function withFallback(backendCall, demoCall) {
  // En local, on ne retente pas à chaque appel : sur un réseau 2G chaque essai
  // coûte les cinq secondes du délai d'attente. On retente quand l'attente est
  // écoulée — ou tout de suite si le système a annoncé le retour du réseau.
  if (!reseau.tenterLeBackend()) return demoCall();

  try {
    const resultat = await backendCall();
    reseau.backendJoignable();
    return resultat;
  } catch (err) {
    if (err instanceof ApiError) {
      // Le backend a répondu, et il a répondu une erreur métier. Il est donc
      // joignable : c'est une information sur le réseau, pas seulement sur la
      // requête. Ne pas la prendre en compte laissait l'application en local
      // alors que le serveur allait bien.
      reseau.backendJoignable();
      throw err;
    }
    reseau.reseauEchoue();
    return demoCall();
  }
}

export const api = {
  chat: (message) =>
    withFallback(
      () => request("/api/chat", { method: "POST", body: JSON.stringify({ message }) }),
      () => demo.chat(message)
    ),
  products: () =>
    withFallback(() => request("/api/products"), () => demo.products()),
  salesSummary: (days = 7) =>
    withFallback(() => request(`/api/sales/summary?days=${days}`), () => demo.salesSummary(days)),
  sales: (limit = 50) =>
    withFallback(() => request(`/api/sales?limit=${limit}`), () => demo.sales(limit)),
  reconcile: (smsText) =>
    withFallback(
      () =>
        request("/api/reconciliation", {
          method: "POST",
          body: JSON.stringify({ sms_text: smsText }),
        }),
      () => demo.reconcile(smsText)
    ),
};
