// Où l'on décide si l'on parle au backend ou aux données de l'appareil.
//
// Le défaut corrigé ici : `lib/api.js` portait un booléen `demoMode` passé à
// `true` au premier échec réseau et **jamais remis à false**. Une coupure de
// cinq secondes — la norme sur un réseau 2G intermittent, qui est la cible de
// `VISION.md §4` — faisait donc basculer l'application en local pour TOUTE la
// session. Le réseau revenait, l'application ne le voyait pas. Le commerçant
// continuait de travailler sur son appareil, et le serveur ne recevait plus
// rien jusqu'au rechargement de la page.
//
// La doctrine dit : « l'app fonctionne sans connexion et SE SYNCHRONISE QUAND
// ELLE REVIENT ». Il manquait le retour.
//
// Ce module ne fait qu'une chose : dire quand retenter. Il ne synchronise rien
// — ça, c'est une question d'architecture posée à Steeve (Q22).

/** Attente après la première coupure. Court : le réseau revient souvent vite. */
export const ATTENTE_INITIALE_MS = 15_000;

/** Plafond. Un déploiement de démonstration n'a pas de backend du tout : sans
 *  plafond il sonderait indéfiniment toutes les 15 s, cinq secondes durant. */
export const ATTENTE_MAX_MS = 5 * 60_000;

export function creerEtatReseau({ maintenant = () => Date.now() } = {}) {
  let local = false;
  let attente = ATTENTE_INITIALE_MS;
  let prochainEssai = 0;

  return {
    /** Est-on en mode local ? */
    estLocal: () => local,

    /** Doit-on tenter le backend maintenant ? */
    tenterLeBackend: () => !local || maintenant() >= prochainEssai,

    /** Le backend a répondu — y compris par une erreur métier : il est joignable. */
    backendJoignable() {
      local = false;
      attente = ATTENTE_INITIALE_MS;
      prochainEssai = 0;
    },

    /** Le réseau a échoué. On repasse en local, avec une attente qui double. */
    reseauEchoue() {
      if (local) attente = Math.min(attente * 2, ATTENTE_MAX_MS);
      local = true;
      prochainEssai = maintenant() + attente;
    },

    /** Le système annonce que la connexion est revenue : on retente tout de suite. */
    connexionAnnoncee() {
      prochainEssai = 0;
      attente = ATTENTE_INITIALE_MS;
    },

    /** Pour les tests et l'affichage. */
    attenteCourante: () => attente,
  };
}
