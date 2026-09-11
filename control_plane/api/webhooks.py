from fastapi import APIRouter, Request
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/api/webhooks")
async def ingest_failure_telemetry(request: Request):
    """Receives the physical TCP payload from the target application."""
    payload = await request.json()
    trace_id = payload.get("trace_id", "UNKNOWN")
    
    # TODO: Pass payload to LangGraph IngestSpanNode
    print(f"WEBHOOK INGESTED - Trace ID: {trace_id}")
    
    return {"status": "ingested", "trace_id": trace_id}
