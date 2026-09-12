"""Limite de débit pour les endpoints qui appellent le modèle.

Pourquoi ce fichier existe
--------------------------
`/api/chat` n'a ni authentification ni limite. Il appelle Claude avec la clé
du projet, et l'agent qu'il pilote dispose d'outils qui **écrivent** :
`add_product`, `adjust_stock`, `record_sale`, `reconcile_momo`. Sans garde-fou,
quiconque atteint l'API peut à la fois vider le crédit d'API et modifier le
stock d'un commerçant.

Le CLAUDE.md du portefeuille fixe la règle : *« Tout endpoint touchant
Anthropic/OpenAI doit avoir un rate limit. Max 20 requêtes/utilisateur/heure. »*

Ce que ce module fait — et ne fait pas
--------------------------------------
Un compteur à fenêtre fixe, en mémoire du processus. C'est délibérément simple :
le déploiement visé (`render.yaml`) est mono-instance, et une dépendance de plus
serait payée par tous les `pip install` pour un besoin que trente lignes
couvrent.

Ce n'est **pas** une limite partagée entre instances. Le jour où le service
passe à plusieurs répliques, il faudra un compteur externe (Redis) — le point
d'entrée `verifier_quota()` ne changera pas, seul son intérieur.

Ce n'est pas non plus de l'authentification : l'adresse IP est usurpable. Elle
borne l'abus le plus courant — une boucle depuis une seule machine — pas un
attaquant décidé.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from fastapi import HTTPException, Request

# Règle CLAUDE.md : 20 requêtes par utilisateur et par heure sur les endpoints IA.
LIMITE_PAR_FENETRE = 20
FENETRE_SECONDES = 3600


@dataclass
class _Compteur:
    """Nombre d'appels vus, et l'instant où la fenêtre courante se referme."""

    appels: int
    fin_fenetre: float


_compteurs: dict[str, _Compteur] = {}
# Uvicorn sert les endpoints synchrones dans un pool de threads : sans verrou,
# deux requêtes simultanées peuvent lire le même compteur et n'en incrémenter
# qu'un seul.
_verrou = threading.Lock()


def identifiant_client(request: Request) -> str:
    """Le meilleur identifiant disponible : l'IP transmise par le proxy.

    Render et la plupart des hébergeurs placent l'adresse réelle en tête de
    `X-Forwarded-For`. On ne retient que la première valeur : les suivantes
    sont ajoutées par les proxys traversés et sont tout aussi usurpables.
    """
    transmise = request.headers.get("x-forwarded-for")
    if transmise:
        premiere = transmise.split(",")[0].strip()
        if premiere:
            return premiere
    reelle = request.headers.get("x-real-ip")
    if reelle and reelle.strip():
        return reelle.strip()
    return request.client.host if request.client else "inconnu"


def _purger(maintenant: float) -> None:
    """Oublie les fenêtres expirées — sinon le dictionnaire croît sans fin."""
    for cle in [c for c, v in _compteurs.items() if v.fin_fenetre <= maintenant]:
        del _compteurs[cle]


def etat_quota(identifiant: str, maintenant: float | None = None) -> tuple[int, int]:
    """Compte les appels de cet identifiant et consomme une unité.

    Retourne `(appels_apres_cet_appel, secondes_avant_reouverture)`.
    Séparé de la dépendance FastAPI pour être testable sans requête HTTP.
    """
    maintenant = time.monotonic() if maintenant is None else maintenant
    with _verrou:
        _purger(maintenant)
        compteur = _compteurs.get(identifiant)
        if compteur is None or compteur.fin_fenetre <= maintenant:
            compteur = _Compteur(appels=0, fin_fenetre=maintenant + FENETRE_SECONDES)
            _compteurs[identifiant] = compteur
        compteur.appels += 1
        return compteur.appels, max(1, int(compteur.fin_fenetre - maintenant))


def reinitialiser() -> None:
    """Vide les compteurs. Réservé aux tests."""
    with _verrou:
        _compteurs.clear()


def verifier_quota(request: Request) -> None:
    """Dépendance FastAPI : lève 429 quand le quota est dépassé."""
    appels, avant_reouverture = etat_quota(identifiant_client(request))
    if appels > LIMITE_PAR_FENETRE:
        minutes = max(1, avant_reouverture // 60)
        raise HTTPException(
            status_code=429,
            detail=(
                f"Limite de {LIMITE_PAR_FENETRE} requêtes par heure atteinte. "
                f"Réessayez dans {minutes} minute(s)."
            ),
            headers={
                "Retry-After": str(avant_reouverture),
                "RateLimit-Limit": str(LIMITE_PAR_FENETRE),
                "RateLimit-Remaining": "0",
            },
        )
