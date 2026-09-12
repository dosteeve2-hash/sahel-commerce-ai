"""Ce que la limite de débit doit garantir.

Le défaut qu'elle ferme : `/api/chat` appelle Claude avec la clé du projet et
pilote un agent qui peut écrire en base. Sans quota, une boucle depuis une
seule machine vide le crédit d'API et modifie le stock d'un commerçant.
"""
import pytest
from fastapi.testclient import TestClient

from app import rate_limit
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def compteurs_vierges():
    rate_limit.reinitialiser()
    yield
    rate_limit.reinitialiser()


def _chat(ip: str = "41.203.0.1"):
    return client.post("/api/chat", json={"message": "bonjour"}, headers={"X-Forwarded-For": ip})


class TestQuota:
    def test_1_les_20_premieres_passent(self):
        for i in range(rate_limit.LIMITE_PAR_FENETRE):
            assert _chat().status_code != 429, f"la requête {i + 1} a été refusée trop tôt"

    def test_2_la_21e_est_refusee(self):
        for _ in range(rate_limit.LIMITE_PAR_FENETRE):
            _chat()
        assert _chat().status_code == 429

    def test_3_le_refus_dit_quand_reessayer(self):
        for _ in range(rate_limit.LIMITE_PAR_FENETRE):
            _chat()
        refus = _chat()
        assert refus.headers["Retry-After"].isdigit()
        assert int(refus.headers["Retry-After"]) > 0
        assert refus.headers["RateLimit-Limit"] == str(rate_limit.LIMITE_PAR_FENETRE)
        assert "minute" in refus.json()["detail"]

    def test_4_le_quota_est_par_client_pas_global(self):
        for _ in range(rate_limit.LIMITE_PAR_FENETRE + 1):
            _chat(ip="41.203.0.1")
        # Un commerçant qui abuse ne doit pas bloquer son voisin.
        assert _chat(ip="41.203.0.2").status_code != 429

    def test_5_les_autres_endpoints_ne_sont_pas_limites(self):
        # Seul /api/chat appelle le modèle : /api/health doit rester libre.
        for _ in range(rate_limit.LIMITE_PAR_FENETRE + 5):
            assert client.get("/api/health").status_code == 200


class TestIdentification:
    def _requete(self, headers: dict):
        from starlette.requests import Request

        portee = {
            "type": "http",
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
            "client": ("10.0.0.1", 1234),
        }
        return Request(portee)

    def test_6_prend_la_premiere_ip_de_x_forwarded_for(self):
        # Les suivantes sont ajoutées par les proxys traversés.
        req = self._requete({"X-Forwarded-For": "41.203.0.1, 10.1.1.1, 10.2.2.2"})
        assert rate_limit.identifiant_client(req) == "41.203.0.1"

    def test_7_se_rabat_sur_x_real_ip(self):
        req = self._requete({"X-Real-IP": "41.203.0.9"})
        assert rate_limit.identifiant_client(req) == "41.203.0.9"

    def test_8_se_rabat_sur_l_adresse_de_la_connexion(self):
        assert rate_limit.identifiant_client(self._requete({})) == "10.0.0.1"

    def test_9_un_x_forwarded_for_vide_ne_fait_pas_planter(self):
        req = self._requete({"X-Forwarded-For": "  "})
        assert rate_limit.identifiant_client(req) == "10.0.0.1"


class TestFenetre:
    def test_10_la_fenetre_se_rouvre_apres_une_heure(self):
        t = 1000.0
        for _ in range(rate_limit.LIMITE_PAR_FENETRE):
            rate_limit.etat_quota("client", maintenant=t)
        appels, _ = rate_limit.etat_quota("client", maintenant=t)
        assert appels > rate_limit.LIMITE_PAR_FENETRE

        plus_tard = t + rate_limit.FENETRE_SECONDES + 1
        appels, _ = rate_limit.etat_quota("client", maintenant=plus_tard)
        assert appels == 1, "la fenêtre aurait dû se rouvrir"

    def test_11_les_fenetres_expirees_sont_purgees(self):
        rate_limit.etat_quota("ephemere", maintenant=1000.0)
        assert "ephemere" in rate_limit._compteurs
        # Un autre client bien plus tard doit déclencher la purge.
        rate_limit.etat_quota("autre", maintenant=1000.0 + rate_limit.FENETRE_SECONDES + 1)
        assert "ephemere" not in rate_limit._compteurs, "le dictionnaire croîtrait sans fin"

    def test_12_le_delai_annonce_decroit_avec_le_temps(self):
        t = 1000.0
        _, debut = rate_limit.etat_quota("client", maintenant=t)
        _, milieu = rate_limit.etat_quota("client", maintenant=t + 1800)
        assert milieu < debut
        assert milieu >= 1
