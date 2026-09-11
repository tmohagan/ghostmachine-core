import subprocess
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class SandboxResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str

def run_isolated_test(test_path: str, repo_path: str) -> SandboxResult:
    """Executes a test file inside an ephemeral, resource-fenced Docker sandbox."""
    logger.info(f"Allocating isolated kernel namespace for {test_path}...")
    
    # Send execution signal to the Docker socket with strict physical bounds
    cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", "2048m",
        "--cpus", "2.0",
        "-v", f"{repo_path}:/workspace",
        "-w", "/workspace",
        "python:3.11-slim",
        "pytest", test_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return SandboxResult(
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr
        )
    except subprocess.TimeoutExpired:
        return SandboxResult(
            exit_code=-1,
            stdout="",
            stderr="Execution exceeded 60s physical timeout limit."
        )
