from typing import TypedDict, Annotated, List, Optional
import operator

class IncidentState(TypedDict):
    trace_id: str
    incident_id: Optional[str]
    exception_class: str
    stack_frames: List[dict]
    
    # The Repro Synthesis Node will write the test path here
    repro_test_path: Optional[str]
    
    # The Patch Generation Node will write the unified diff here
    proposed_patch: Optional[str]
    
    # The Sandbox Execution Node will record the final exit code
    sandbox_exit_code: Optional[int]
    
    # Guardrail validation results
    guardrail_status: Optional[str]
    guardrail_reason: Optional[str]

    # PR staging results
    pr_url: Optional[str]
    pr_error: Optional[str]

    # Telemetry and cost tracking
    total_tokens: Optional[int]
    compute_seconds: Optional[float]

    # Post-mortem report fields
    root_cause: Optional[str]
    affected_endpoints: Optional[str]
    downtime_ms: Optional[int]
    timestamp_ingest: Optional[str]
    timestamp_patch: Optional[str]
    timestamp_success: Optional[str]
    five_whys: Optional[str]
    recommendations: Optional[str]

    # Orchestrator tracking (Max 3 recursive attempts per policy)
    recursion_count: Annotated[int, operator.add]
