from fastapi import APIRouter

from ..models import ReconcileIn, ReconcileReport
from ..services import momo

router = APIRouter(prefix="/api/reconciliation", tags=["reconciliation"])


@router.post("", response_model=ReconcileReport)
def reconcile(payload: ReconcileIn):
    return momo.reconcile(payload.sms_text)
