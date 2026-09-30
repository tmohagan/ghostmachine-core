import os
import secrets
import asyncio
import hashlib
import redis.asyncio as redis
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
    config = {"configurable": {"thread_id": payload.trace_id}}
    orchestrator_app.invoke(initial_state, config=config)

@router.post("/api/webhooks", dependencies=[Depends(verify_webhook_secret)])
async def ingest_webhook(payload: AlertPayload, background_tasks: BackgroundTasks):
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    try:
        redis_client = redis.from_url(redis_url)
        
        # Hash the signature: exception class + top 5 stack frames
        traceback_lines = payload.traceback.splitlines()
        top_frames = "\n".join(traceback_lines[:5])
        signature = f"{payload.error_class}:{top_frames}"
        signature_hash = hashlib.sha256(signature.encode("utf8")).hexdigest()
        
        dedup_key = f"dedup:incident:{signature_hash}"
        
        # Try to set the key with a 15 minute TTL
        is_new = await redis_client.set(dedup_key, "1", nx=True, ex=900)
        
        await redis_client.aclose()
        
        if not is_new:
            return {"status": "dropped", "reason": "duplicate", "trace_id": payload.trace_id}
            
    except Exception as e:
        # Fail open if Redis is unavailable
        print(f"Redis deduplication failed: {e}")
        pass

    background_tasks.add_task(run_remediation, payload)
    return {"status": "processing", "trace_id": payload.trace_id}
