from fastapi import APIRouter, Request
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class AlertPayload(BaseModel):
    trace_id: str
    span_id: str
    exception_class: str
    stack_frames: list

@router.post("/webhook/ingest")
async def ingest_span(payload: AlertPayload, request: Request):
    # Mechanism: TCP buffer -> LangGraph Ingest Node
    logger.info(f"Trace {payload.trace_id} ingested. Awaiting state machine execution.")
    return {"status": "ingested", "trace_id": payload.trace_id}
