from fastapi import APIRouter

from ..agent.core import run_agent
from ..models import ChatIn, ChatOut

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatOut)
def chat(payload: ChatIn) -> ChatOut:
    result = run_agent(payload.message)
    return ChatOut(**result)
