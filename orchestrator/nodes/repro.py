import os
from google import genai
from orchestrator.state import IncidentState

def get_genai_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)

def repro_synthesis_node(state: IncidentState) -> dict:
    trace_id = state["trace_id"]
    test_rel_path = f"tests/incidents/test_reproduce_{trace_id}.py"
    repo_path = os.environ.get("CMS_REPO_PATH", "/home/tim/workspace/tim-ohagan-cms")
    
    prompt = f"""You are an automated SRE test engineering system.
Generate a self-contained pytest test using httpx to reproduce the following application failure.
Target endpoint base URL is http://cms-app:8000.

Exception: {state['exception_class']}
Stack Trace:
{chr(10).join(state['stack_frames'])}

Requirements:
- Output ONLY valid Python code. Do not wrap in markdown tags or backticks.
- Import pytest and httpx.
- The test must send the request payload or trigger the condition that reproduces the error.
- Function name must be test_reproduce_incident().
"""
    client = get_genai_client()
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )
    
    code = response.text.strip().removeprefix("```python").removesuffix("```").strip()
    
    # Write to target CMS repository
    target_file = os.path.join(repo_path, test_rel_path)
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    with open(target_file, "w") as f:
        f.write(code)
    
    # Also write locally if repo_path differs
    if repo_path != os.getcwd():
        os.makedirs(os.path.dirname(test_rel_path), exist_ok=True)
        with open(test_rel_path, "w") as f:
            f.write(code)
        
    return {"repro_test_path": test_rel_path}
