"""Sahel Commerce AI — API principale.

Lancement local :
    cd backend
    pip install -r requirements.txt
    uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .db import init_db
from .routers import chat, products, reconciliation, sales

app = FastAPI(
    title="Sahel Commerce AI",
    description="Assistant IA de gestion commerciale pour commerçants d'Afrique de l'Ouest",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(chat.router)
app.include_router(products.router)
app.include_router(sales.router)
app.include_router(reconciliation.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
