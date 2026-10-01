import os
import re
from google import genai
from orchestrator.state import IncidentState

def get_genai_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)

def extract_file_context(stack_frames: list[str]) -> str:
    cms_repo_path = os.environ.get("CMS_REPO_PATH")
    if not cms_repo_path:
        return ""
    
    context = []
    pattern = re.compile(r'File "([^"]+)", line (\d+)')
    seen_files = set()
    
    for line in stack_frames:
        match = pattern.search(line)
        if match:
            file_path = match.group(1)
            line_num = int(match.group(2))
            
            local_file = None
            if os.path.exists(file_path):
                local_file = file_path
            else:
                clean_path = file_path.lstrip('/')
                parts = clean_path.split('/')
                for i in range(len(parts)):
                    test_path = os.path.join(cms_repo_path, *parts[i:])
                    if os.path.exists(test_path):
                        local_file = test_path
                        break
            
            if local_file and (local_file, line_num) not in seen_files:
                seen_files.add((local_file, line_num))
                try:
                    with open(local_file, 'r') as f:
                        lines = f.readlines()
                        start = max(0, line_num - 15)
                        end = min(len(lines), line_num + 15)
                        snippet = "".join(lines[start:end])
                        rel_path = os.path.relpath(local_file, cms_repo_path)
                        context.append(f"\n--- {rel_path} (Lines {start+1}-{end}) ---\n{snippet}")
                except Exception:
                    pass
                    
    if context:
        return "\n\nLocal Code Context:" + "".join(context)
    return ""

def patch_generation_node(state: IncidentState) -> dict:
    trace_id = state["trace_id"]
    recursion_count = state.get("recursion_count", 0)
    
    file_context = extract_file_context(state['stack_frames'])
    
    prompt = f"""You are an autonomous SRE patch engineer.
Generate a minimal unified git diff (patch) to fix the following software defect.

Error: {state['exception_class']}
Traceback:
{chr(10).join(state['stack_frames'])}{file_context}
"""

    if recursion_count > 0:
        feedback = ""
        if state.get("guardrail_status") == "failed":
            feedback = f"YOUR PREVIOUS PATCH FAILED SYNTAX GUARDRAILS:\nReason: {state.get('guardrail_reason')}\n"
        elif state.get("sandbox_exit_code") not in (None, 0):
            feedback = f"YOUR PREVIOUS PATCH FAILED REGRESSION TESTS.\nThe patch did not fix the bug or broke existing tests.\n"
        
        if feedback and state.get("proposed_patch"):
            prompt += f"\n{feedback}Previous Patch:\n{state.get('proposed_patch')}\n\nPlease analyze the failure and generate a NEW patch.\n"

    prompt += """
Rules:
1. Return ONLY the raw unified git diff format. No conversational text or markdown code fences.
2. The patch MUST NOT exceed 80 lines.
3. DO NOT include bare except blocks (ExceptHandler:name=None).
4. Do not alter authentication dependencies or database migrations.
"""
    client = get_genai_client()
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )
    
    patch = response.text.strip().removeprefix("```diff").removesuffix("```").strip()
    return {
        "proposed_patch": patch,
        "recursion_count": recursion_count + 1
    }
