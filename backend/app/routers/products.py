from fastapi import APIRouter, HTTPException

from ..models import Product, ProductIn
from ..services import inventory

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[Product])
def list_products():
    return inventory.list_products()


@router.post("", response_model=Product, status_code=201)
def create_product(payload: ProductIn):
    try:
        return inventory.add_product(payload.name, payload.price, payload.stock)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/low-stock", response_model=list[Product])
def low_stock(threshold: int = 5):
    return inventory.low_stock(threshold)
