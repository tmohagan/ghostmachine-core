from typing import TypedDict, Annotated, List, Optional
import operator

class IncidentState(TypedDict):
    trace_id: str
    exception_class: str
    stack_frames: List[dict]
    
    # The Repro Synthesis Node will write the test path here
    repro_test_path: Optional[str]
    
    # The Patch Generation Node will write the unified diff here
    proposed_patch: Optional[str]
    
    # The Sandbox Execution Node will record the final exit code
    sandbox_exit_code: Optional[int]
    
    # Orchestrator tracking (Max 3 recursive attempts per policy)
    recursion_count: Annotated[int, operator.add]
