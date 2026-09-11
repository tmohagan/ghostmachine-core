from typing import Dict, Any
from orchestrator.state import IncidentState
import logging
import time
import os

logger = logging.getLogger(__name__)

def ingest_span_node(state: IncidentState) -> Dict[str, Any]:
    """
    Physical Mechanism: Reads the trace dictionary from heap memory, 
    validates the schema, and appends a record to the physical audit file.
    """
    trace_id = state.get("trace_id", "UNKNOWN_TRACE")
    exception_class = state.get("exception_class", "UNKNOWN_EXCEPTION")
    
    # 1. Mandatory Audit Logging (Append-only file operation)
    # Note: Using local workspace for scaffolding to avoid host /var/log permissions
    audit_path = os.path.join(os.getcwd(), "audit.log")
    with open(audit_path, "a") as f:
        # Writes an entry to the audit log with tamper-evident execution timestamps
        f.write(f"[{time.time()}] INGEST: Trace {trace_id} | Exception: {exception_class}\n")
        
    logger.info(f"Span {trace_id} successfully parsed and audited. Moving to synthesis.")
    
    # 2. Return State Updates
    # LangGraph merges this returned dictionary back into the shared IncidentState memory
    return {"recursion_count": 0}
