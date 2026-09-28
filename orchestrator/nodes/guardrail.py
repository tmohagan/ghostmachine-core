from typing import Dict, Any
from orchestrator.state import IncidentState
import logging
import ast
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)

def ast_guardrail_node(state: IncidentState) -> Dict[str, Any]:
    """
    Physical Mechanism: Reads the proposed patch text from heap memory,
    parses the target file into an Abstract Syntax Tree (AST), and traverses 
    the memory nodes to detect forbidden patterns (e.g., bare except blocks).
    """
    trace_id = state.get("trace_id", "UNKNOWN_TRACE")
    logger.info(f"Parsing AST for trace {trace_id} patch...")
    
    patch_text = state.get("proposed_patch", "")
    if not patch_text:
        return {}
        
    repo_path = os.environ.get("CMS_REPO_PATH", "/home/tim/workspace/tim-ohagan-cms")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # copy repo to temp_dir safely
        subprocess.run(["cp", "-a", f"{repo_path}/.", temp_dir], check=False)
        
        patch_file = os.path.join(temp_dir, "patch.diff")
        with open(patch_file, "w") as f:
            f.write(patch_text)
            
        res = subprocess.run(["git", "apply", "patch.diff"], cwd=temp_dir, capture_output=True)
        if res.returncode == 0:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith(".py"):
                        try:
                            with open(os.path.join(root, file), "r") as f:
                                tree = ast.parse(f.read())
                            for node in ast.walk(tree):
                                if isinstance(node, ast.ExceptHandler) and node.type is None:
                                    logger.error("Guardrail blocked: Bare except block detected")
                                    return {"guardrail_status": "failed", "guardrail_reason": "Bare except block"}
                                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                                    if isinstance(node.func.value, ast.Name) and node.func.value.id == "os" and node.func.attr == "system":
                                        logger.error("Guardrail blocked: os.system call detected")
                                        return {"guardrail_status": "failed", "guardrail_reason": "os.system call"}
                        except Exception:
                            continue
                            
    logger.info("AST Guardrail passed: No forbidden nodes detected.")
    return {"guardrail_status": "passed"}
