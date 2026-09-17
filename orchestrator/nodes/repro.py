import os
from google import genai
from orchestrator.state import IncidentState

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

def repro_synthesis_node(state: IncidentState) -> dict:
    trace_id = state["trace_id"]
    test_path = f"tests/incidents/test_reproduce_{trace_id}.py"
    
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
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    code = response.text.strip().removeprefix("```python").removesuffix("```").strip()
    
    os.makedirs(os.path.dirname(test_path), exist_ok=True)
    with open(test_path, "w") as f:
        f.write(code)
        
    return {"repro_test_path": test_path}
