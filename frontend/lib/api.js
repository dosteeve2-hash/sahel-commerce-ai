// Client API avec bascule automatique : backend FastAPI si joignable,
// sinon mode démo navigateur (lib/demo.js, données locales).

import * as demo from "./demo";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let demoMode = false;

export function isDemoMode() {
  return demoMode;
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
  if (demoMode) return demoCall();
  try {
    return await backendCall();
  } catch (err) {
    if (err instanceof ApiError) throw err; // backend joignable : vraie erreur métier
    demoMode = true; // réseau KO : bascule en démo navigateur
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
