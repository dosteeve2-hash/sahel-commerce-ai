from fastapi import APIRouter, Depends

from ..agent.core import run_agent
from ..models import ChatIn, ChatOut
from ..rate_limit import verifier_quota

router = APIRouter(prefix="/api/chat", tags=["chat"])


# `verifier_quota` s'exécute avant le corps : c'est le seul endpoint qui appelle
# le modèle, et le seul dont l'agent puisse écrire en base (adjust_stock,
# record_sale). Sans quota, un seul client peut vider le crédit d'API et
# modifier le stock d'un commerçant.
@router.post("", response_model=ChatOut, dependencies=[Depends(verifier_quota)])
def chat(payload: ChatIn) -> ChatOut:
    result = run_agent(payload.message)
    return ChatOut(**result)
