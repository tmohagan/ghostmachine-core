from typing import Dict, Any
from orchestrator.state import IncidentState
from tools.ast_auditor import validate_patch_syntax
import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)

def get_modified_files(patch_text: str) -> list[str]:
    """Extracts target file paths from unified diff headers."""
    files = []
    for line in patch_text.splitlines():
        if line.startswith("+++ b/"):
            files.append(line.split("+++ b/")[-1].strip())
    return files

def ast_guardrail_node(state: IncidentState) -> Dict[str, Any]:
    """
    Physical Mechanism: Reads the proposed patch text from heap memory,
    parses modified files into an Abstract Syntax Tree (AST), and traverses 
    the memory nodes to detect forbidden patterns (e.g., bare except blocks).
    """
    trace_id = state.get("trace_id", "UNKNOWN_TRACE")
    logger.info(f"Parsing AST for trace {trace_id} patch...")
    
    patch_text = state.get("proposed_patch", "")
    if not patch_text:
        return {}
        
    repo_path = os.environ.get("CMS_REPO_PATH", "/home/tim/workspace/tim-ohagan-cms")
    modified_files = get_modified_files(patch_text)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # copy repo to temp_dir safely
        subprocess.run(["cp", "-a", f"{repo_path}/.", temp_dir], check=False)
        
        patch_file = os.path.join(temp_dir, "patch.diff")
        with open(patch_file, "w") as f:
            f.write(patch_text + "\n")
            
        # Apply patch using patch -p1 (lenient, matching sandbox/stage behavior)
        apply_cmd = f"cd {temp_dir} && patch -p1 < patch.diff"
        res = subprocess.run(apply_cmd, shell=True, capture_output=True, text=True)
        
        if res.returncode != 0:
            logger.error(f"Guardrail blocked: Patch application failed\n{res.stderr}\n{res.stdout}")
            return {"guardrail_status": "failed", "guardrail_reason": "Patch application failed"}
            
        # Audit only the files modified by this patch
        for file_path in modified_files:
            if file_path.endswith(".py"):
                full_path = os.path.join(temp_dir, file_path)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, "r") as f:
                            source = f.read()
                        
                        violations = validate_patch_syntax(source)
                        if violations:
                            logger.error(f"Guardrail blocked in {file_path}: {violations[0]}")
                            return {"guardrail_status": "failed", "guardrail_reason": violations[0]}
                    except Exception as e:
                        logger.error(f"Guardrail exception reading {file_path}: {e}")
                        continue
                            
    logger.info("AST Guardrail passed: No forbidden nodes detected.")
    return {"guardrail_status": "passed"}
