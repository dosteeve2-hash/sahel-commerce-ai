import { describe, expect, it } from "vitest";

import {
  ATTENTE_INITIALE_MS,
  ATTENTE_MAX_MS,
  creerEtatReseau,
} from "../lib/reseau";

/** Horloge contrôlée : ces tests parlent de délais, pas de vitesse d'exécution. */
function horloge(depart = 0) {
  let t = depart;
  return { maintenant: () => t, avancer: (ms) => (t += ms) };
}

describe("le retour en ligne", () => {
  it("part en parlant au backend", () => {
    const r = creerEtatReseau();
    expect(r.estLocal()).toBe(false);
    expect(r.tenterLeBackend()).toBe(true);
  });

  // Le défaut corrigé. Avant, un seul échec réseau basculait l'application en
  // local pour toute la session : le booléen n'était jamais remis à false.
  it("REVIENT en ligne une fois l'attente écoulée", () => {
    const h = horloge();
    const r = creerEtatReseau({ maintenant: h.maintenant });

    r.reseauEchoue();
    expect(r.estLocal()).toBe(true);
    expect(r.tenterLeBackend()).toBe(false);

    h.avancer(ATTENTE_INITIALE_MS);
    expect(r.tenterLeBackend()).toBe(true);
  });

  it("ne retente pas avant la fin de l'attente", () => {
    const h = horloge();
    const r = creerEtatReseau({ maintenant: h.maintenant });
    r.reseauEchoue();

    h.avancer(ATTENTE_INITIALE_MS - 1);
    expect(r.tenterLeBackend()).toBe(false);
  });

  it("repasse en ligne quand le backend répond", () => {
    const h = horloge();
    const r = creerEtatReseau({ maintenant: h.maintenant });
    r.reseauEchoue();
    h.avancer(ATTENTE_INITIALE_MS);

    r.backendJoignable();
    expect(r.estLocal()).toBe(false);
    expect(r.tenterLeBackend()).toBe(true);
  });

  it("remet l'attente à zéro après un retour, pour que la coupure suivante soit traitée aussi vite", () => {
    const h = horloge();
    const r = creerEtatReseau({ maintenant: h.maintenant });

    r.reseauEchoue();
    h.avancer(ATTENTE_INITIALE_MS);
    r.reseauEchoue();
    expect(r.attenteCourante()).toBe(ATTENTE_INITIALE_MS * 2);

    r.backendJoignable();
    expect(r.attenteCourante()).toBe(ATTENTE_INITIALE_MS);
  });
});

describe("l'attente double, et elle est plafonnée", () => {
  // Sans plafond, un déploiement de démonstration — qui n'a AUCUN backend —
  // sonderait indéfiniment, cinq secondes de délai d'attente à chaque fois.
  it("double à chaque échec consécutif", () => {
    const h = horloge();
    const r = creerEtatReseau({ maintenant: h.maintenant });

    r.reseauEchoue();
    expect(r.attenteCourante()).toBe(ATTENTE_INITIALE_MS);
    r.reseauEchoue();
    expect(r.attenteCourante()).toBe(ATTENTE_INITIALE_MS * 2);
    r.reseauEchoue();
    expect(r.attenteCourante()).toBe(ATTENTE_INITIALE_MS * 4);
  });

  it("ne dépasse jamais le plafond", () => {
    const h = horloge();
    const r = creerEtatReseau({ maintenant: h.maintenant });
    for (let i = 0; i < 50; i++) r.reseauEchoue();
    expect(r.attenteCourante()).toBe(ATTENTE_MAX_MS);
  });
});

describe("l'événement « online » du navigateur", () => {
  it("fait retenter immédiatement, sans attendre le délai", () => {
    const h = horloge();
    const r = creerEtatReseau({ maintenant: h.maintenant });
    r.reseauEchoue();
    expect(r.tenterLeBackend()).toBe(false);

    r.connexionAnnoncee();
    expect(r.tenterLeBackend()).toBe(true);
  });

  it("remet aussi l'attente à son minimum", () => {
    const h = horloge();
    const r = creerEtatReseau({ maintenant: h.maintenant });
    r.reseauEchoue();
    r.reseauEchoue();
    r.reseauEchoue();
    expect(r.attenteCourante()).toBe(ATTENTE_INITIALE_MS * 4);

    r.connexionAnnoncee();
    expect(r.attenteCourante()).toBe(ATTENTE_INITIALE_MS);
  });
});

describe("une erreur métier n'est pas une panne de réseau", () => {
  // Le backend qui répond « produit introuvable » est un backend JOIGNABLE.
  // Le traiter comme une coupure laissait l'application en local alors que le
  // serveur allait très bien.
  it("un backend qui répond une erreur compte comme joignable", () => {
    const h = horloge();
    const r = creerEtatReseau({ maintenant: h.maintenant });
    r.reseauEchoue();

    r.backendJoignable();
    expect(r.estLocal()).toBe(false);
  });
});
