import docker
import os
from orchestrator.state import IncidentState

docker_client = docker.from_env()

def sandbox_execution_node(state: IncidentState) -> dict:
    repo_path = os.environ.get("CMS_REPO_PATH", "/home/tim/workspace/tim-ohagan-cms")
    test_file = state.get("repro_test_path")
    
    volumes = {
        repo_path: {"bind": "/app", "mode": "rw"}
    }
    
    # Apply proposed patch inside working tree if available
    patch_content = state.get("proposed_patch")
    if patch_content:
        patch_file_path = os.path.join(repo_path, "current_fix.patch")
        with open(patch_file_path, "w") as f:
            f.write(patch_content)
        
        # Apply patch via git
        os.system(f"cd {repo_path} && git apply current_fix.patch")
        if os.path.exists(patch_file_path):
            os.remove(patch_file_path)

    cmd = f"poetry run pytest {test_file}"
    
    try:
        container = docker_client.containers.run(
            image="python:3.11-slim",
            command=f"bash -c 'poetry install --no-root && {cmd}'",
            volumes=volumes,
            working_dir="/app",
            network_disabled=True,
            mem_limit="2048m",
            nano_cpus=2000000000,
            remove=True,
            detach=False
        )
        exit_code = 0
    except docker.errors.ContainerError as exc:
        exit_code = exc.exit_status

    return {"sandbox_exit_code": exit_code}
    
