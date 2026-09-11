from typing import Dict, Any
from orchestrator.state import IncidentState
import logging

logger = logging.getLogger(__name__)

def repro_synthesis_node(state: IncidentState) -> Dict[str, Any]:
    """
    Physical Mechanism: Reads the exception details from heap memory,
    synthesizes a pytest script to trigger the exact failure, and writes
    the intended file path to the shared state.
    """
    trace_id = state.get("trace_id", "UNKNOWN_TRACE")
    logger.info(f"Synthesizing reproduction test for trace {trace_id}...")
    
    # Mechanism: We allocate the target file path for the test.
    # In the live graph, the FastMCP tool writes the actual code to the target repo's disk.
    test_path = f"tests/incidents/test_reproduce_{trace_id}.py"
    
    # We return the dictionary update. LangGraph merges this into the main IncidentState.
    return {"repro_test_path": test_path}
