import os
from google import genai
from orchestrator.state import IncidentState

def get_genai_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)

def patch_generation_node(state: IncidentState) -> dict:
    trace_id = state["trace_id"]
    recursion_count = state.get("recursion_count", 0)
    
    prompt = f"""You are an autonomous SRE patch engineer.
Generate a minimal unified git diff (patch) to fix the following software defect.

Error: {state['exception_class']}
Traceback:
{chr(10).join(state['stack_frames'])}

Rules:
1. Return ONLY the raw unified git diff format. No conversational text or markdown code fences.
2. The patch MUST NOT exceed 80 lines.
3. DO NOT include bare except blocks (ExceptHandler:name=None).
4. Do not alter authentication dependencies or database migrations.
"""
    client = get_genai_client()
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )
    except Exception:
        response = client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents=prompt
        )
    
    patch = response.text.strip().removeprefix("```diff").removesuffix("```").strip()
    return {
        "proposed_patch": patch,
        "recursion_count": recursion_count + 1
    }
