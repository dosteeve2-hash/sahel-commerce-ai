from fastapi import APIRouter, HTTPException

from ..models import Sale, SaleIn
from ..services import sales as sales_service

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.get("", response_model=list[Sale])
def list_sales(limit: int = 50):
    return sales_service.list_sales(limit)


@router.post("", response_model=Sale, status_code=201)
def create_sale(payload: SaleIn):
    try:
        return sales_service.record_sale(
            payload.product_name, payload.quantity, payload.payment_method, payload.momo_ref
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/summary")
def summary(days: int = 7):
    return sales_service.sales_summary(days)
