import asyncio
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List
from orchestrator.graph import app as orchestrator_app

router = APIRouter()

class AlertPayload(BaseModel):
    trace_id: str
    error_class: str
    traceback: str
    method: str
    url: str

def run_remediation(payload: AlertPayload):
    initial_state = {
        "trace_id": payload.trace_id,
        "exception_class": payload.error_class,
        "stack_frames": payload.traceback.splitlines(),
        "recursion_count": 0,
        "sandbox_exit_code": None,
        "proposed_patch": None,
        "repro_test_path": None,
        "pr_url": None
    }
    orchestrator_app.invoke(initial_state)

@router.post("/api/webhooks")
async def ingest_webhook(payload: AlertPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_remediation, payload)
    return {"status": "processing", "trace_id": payload.trace_id}
