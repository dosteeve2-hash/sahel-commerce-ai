# Guide de démarrage — pour Steeve 🚀

Ce fichier est pour toi (pas pour le repo public — tu peux le supprimer avant de pousser, ou le garder).

## 1. Lancer le projet (10 min)

**Prérequis :** Python 3.10+ et Node.js 18+.

**Backend** (PowerShell) :
```powershell
cd Desktop\sahel-commerce-ai\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python seed.py
uvicorn app.main:app --reload
```
→ Ouvre http://localhost:8000/docs : tu as une doc API interactive automatique (Swagger).

**Frontend** (2e terminal) :
```powershell
cd Desktop\sahel-commerce-ai\frontend
npm install
copy .env.local.example .env.local
npm run dev
```
→ Ouvre http://localhost:3000

**Sans clé API**, l'agent tourne en mode démo (regex). Essaie : « montre le stock », « vends 2 Savon Citec en orange », « bilan ».
**Avec une clé** (console.anthropic.com → mets-la dans `backend/.env`), tu as le vrai agent Claude avec tool-calling.

## 2. Pousser sur GitHub

```powershell
cd Desktop\sahel-commerce-ai
git init
git add .
git commit -m "feat: Sahel Commerce AI v1 — agent IA, inventaire, ventes, réconciliation mobile money"
```
Puis crée le repo `sahel-commerce-ai` sur GitHub et pousse. **Vérifie que `.env` n'est jamais commité** (le `.gitignore` le bloque déjà).

## 3. Déployer (MVP en ligne)

1. **API** → [Render](https://render.com) (gratuit) : nouveau Web Service depuis ton repo, root `backend`, commande `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Ajoute `ANTHROPIC_API_KEY` et `CORS_ORIGINS=https://ton-front.vercel.app` dans les variables d'env.
2. **Frontend** → Vercel : importe le repo, root `frontend`, variable `NEXT_PUBLIC_API_URL=https://ton-api.onrender.com`.
3. Mets l'URL live en haut du README + sur ton portfolio et LinkedIn.

## 4. Ce que ce projet prouve à un recruteur

- **Agent IA réel** : boucle tool-calling maison (`agent/core.py`), pas un simple appel API.
- **Sens produit** : problème africain concret, réconciliation mobile money = feature différenciante que personne d'autre n'a dans son portfolio.
- **Architecture propre** : séparation routers / services / agent, contrats Pydantic, mode dégradé (démo) pensé pour la faible connectivité.
- **Vision** : roadmap claire (WhatsApp, Supabase, vocal Mooré).

## 5. Prochaines étapes ensemble (dans l'ordre)

1. Lancer en local, tester, me signaler tout bug → je corrige avec toi.
2. Déployer (étape 3) → ton premier projet IA **en ligne**.
3. Canal WhatsApp (Twilio sandbox, ~1 session de travail).
4. Migration Supabase + comptes multi-commerçants.
5. Article LinkedIn : « Pourquoi j'ai construit un agent IA pour les commerçants du Faso » — ça, ça attire les recruteurs.
