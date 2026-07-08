"""Schémas Pydantic (contrats d'API)."""
from pydantic import BaseModel, Field


class ProductIn(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(ge=0)
    stock: int = Field(ge=0, default=0)


class Product(ProductIn):
    id: int
    created_at: str


class SaleIn(BaseModel):
    product_name: str
    quantity: int = Field(gt=0)
    payment_method: str = Field(default="cash", pattern="^(cash|orange_money|moov_money)$")
    momo_ref: str | None = None


class Sale(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    total: float
    payment_method: str
    momo_ref: str | None
    created_at: str


class ChatIn(BaseModel):
    message: str = Field(min_length=1)


class ChatOut(BaseModel):
    reply: str
    tools_used: list[str] = []
    demo_mode: bool = False


class ReconcileIn(BaseModel):
    sms_text: str = Field(min_length=1, description="SMS mobile money bruts, un par ligne ou collés en bloc")


class ReconcileReport(BaseModel):
    parsed: int
    matched: int
    unmatched_transactions: list[dict]
    unmatched_sales: list[dict]
