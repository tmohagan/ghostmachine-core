import os
import secrets
import asyncio
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional
from orchestrator.graph import app as orchestrator_app

router = APIRouter()

class AlertPayload(BaseModel):
    trace_id: str
    error_class: str
    traceback: str
    method: str
    url: str

def verify_webhook_secret(
    x_ghostmachine_secret: Optional[str] = Header(None, alias="X-GhostMachine-Secret")
):
    """
    Validates that incoming webhook calls contain the pre-shared secret.
    Mitigates unauthenticated DoS and unauthorized LLM/sandbox invocation.
    """
    expected_secret = os.environ.get("WEBHOOK_SECRET")
    if not expected_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: WEBHOOK_SECRET is not configured."
        )
    
    if not x_ghostmachine_secret or not secrets.compare_digest(
        x_ghostmachine_secret.encode("utf8"), 
        expected_secret.encode("utf8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing X-GhostMachine-Secret header."
        )
    return True

def run_remediation(payload: AlertPayload):
    initial_state = {
        "trace_id": payload.trace_id,
        "incident_id": f"INC-{payload.trace_id[:8].upper()}",
        "exception_class": payload.error_class,
        "stack_frames": payload.traceback.splitlines(),
        "recursion_count": 0,
        "sandbox_exit_code": None,
        "proposed_patch": None,
        "repro_test_path": None,
        "pr_url": None
    }
    orchestrator_app.invoke(initial_state)

@router.post("/api/webhooks", dependencies=[Depends(verify_webhook_secret)])
async def ingest_webhook(payload: AlertPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_remediation, payload)
    return {"status": "processing", "trace_id": payload.trace_id}
