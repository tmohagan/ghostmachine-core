from typing import Dict, Any
from orchestrator.state import IncidentState
import logging

logger = logging.getLogger(__name__)

def patch_generation_node(state: IncidentState) -> Dict[str, Any]:
    """
    Physical Mechanism: Reads the exception and stack trace from heap memory,
    generates a unified text diff (the patch) bounded by the 80-line limit, 
    and writes the string to the shared state.
    """
    trace_id = state.get("trace_id", "UNKNOWN_TRACE")
    logger.info(f"Drafting in-memory patch for trace {trace_id}...")
    
    # Mechanism: We allocate a simulated unified diff string.
    # In the live graph, the LLM generates this strictly bounded to max_diff_lines (80).
    simulated_patch = "--- a/app/api/routes/posts.py\n+++ b/app/api/routes/posts.py\n@@ -10,3 +10,3 @@\n-    pass\n+    return {'status': 'fixed'}\n"
    
    # We return the dictionary update. LangGraph merges this into IncidentState.
    return {"proposed_patch": simulated_patch}
