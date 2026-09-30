from langgraph.graph import StateGraph, END
from orchestrator.state import IncidentState
from orchestrator.nodes.ingest import ingest_span_node
from orchestrator.nodes.repro import repro_synthesis_node
from orchestrator.nodes.sandbox import sandbox_execution_node, sandbox_final_node
from orchestrator.nodes.patcher import patch_generation_node
from orchestrator.nodes.guardrail import ast_guardrail_node
from orchestrator.nodes.stage import staging_canary_node
import logging

logger = logging.getLogger(__name__)

# Mechanism: Initialize the routing table bound to our shared RAM schema
workflow = StateGraph(IncidentState)

# 1. Register the physical function pointers (Nodes)
workflow.add_node("ingest", ingest_span_node)
workflow.add_node("repro", repro_synthesis_node)
workflow.add_node("sandbox_initial", sandbox_execution_node)
workflow.add_node("patch", patch_generation_node)
workflow.add_node("guardrail", ast_guardrail_node)
workflow.add_node("sandbox_final", sandbox_final_node)
workflow.add_node("stage", staging_canary_node)

def guardrail_router(state: IncidentState) -> str:
    status = state.get("guardrail_status")
    if status == "passed":
        return "sandbox_final"
    elif state.get("recursion_count", 0) < 3:
        return "patch"
    else:
        return "end"

def sandbox_router(state: IncidentState) -> str:
    if state.get("sandbox_exit_code") == 0:
        return "stage"
    elif state.get("recursion_count", 0) < 3:
        return "patch"
    else:
        return "end"

# 2. Define the mandatory linear execution path (Edges)
workflow.set_entry_point("ingest")
workflow.add_edge("ingest", "repro")
workflow.add_edge("repro", "sandbox_initial")
workflow.add_edge("sandbox_initial", "patch")
workflow.add_edge("patch", "guardrail")

workflow.add_conditional_edges(
    "guardrail",
    guardrail_router,
    {
        "sandbox_final": "sandbox_final",
        "patch": "patch",
        "end": END
    }
)

workflow.add_conditional_edges(
    "sandbox_final",
    sandbox_router,
    {
        "stage": "stage",
        "patch": "patch",
        "end": END
    }
)

workflow.add_edge("stage", END)

# 3. Compile the graph into an executable process
app = workflow.compile()
logger.info("LangGraph orchestrator compiled successfully.")
