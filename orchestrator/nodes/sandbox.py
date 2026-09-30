import docker
import os
import subprocess
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
            f.write(patch_content + "\n")
        
        # Apply patch leniently, matching stage.py behavior
        apply_cmd = (
            f"git config --global --add safe.directory {repo_path} && "
            f"cd {repo_path} && patch -p1 < current_fix.patch"
        )
        try:
            subprocess.run(apply_cmd, shell=True, capture_output=True, check=False)
        except Exception:
            pass  # Let the test result determine success
        finally:
            if os.path.exists(patch_file_path):
                os.remove(patch_file_path)

    cmd = f"poetry run pytest {test_file}"
    
    try:
        container = docker_client.containers.run(
            image="tim-ohagan-cms-app:latest",
            command=f"poetry run pytest {test_file}",
            volumes=volumes,
            working_dir="/app",
            network="ghostmachine-bridge",
            mem_limit="2048m",
            nano_cpus=2000000000,
            remove=True,
            detach=False
        )
        exit_code = 0
    except docker.errors.ContainerError as exc:
        exit_code = exc.exit_status

    return {"sandbox_exit_code": exit_code}

def sandbox_final_node(state: IncidentState) -> dict:
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
            f.write(patch_content + "\n")
        
        # Apply patch leniently, matching stage.py behavior
        apply_cmd = (
            f"git config --global --add safe.directory {repo_path} && "
            f"cd {repo_path} && patch -p1 < current_fix.patch"
        )
        try:
            subprocess.run(apply_cmd, shell=True, capture_output=True, check=False)
        except Exception:
            pass  # Let the test result determine success
        finally:
            if os.path.exists(patch_file_path):
                os.remove(patch_file_path)

    # Run both the repro test and the full regression test suite
    try:
        container = docker_client.containers.run(
            image="tim-ohagan-cms-app:latest",
            command=f'sh -c "poetry run pytest {test_file} && poetry run pytest"',
            volumes=volumes,
            working_dir="/app",
            network="ghostmachine-bridge",
            mem_limit="2048m",
            nano_cpus=2000000000,
            remove=True,
            detach=False
        )
        exit_code = 0
    except docker.errors.ContainerError as exc:
        exit_code = exc.exit_status

    return {"sandbox_exit_code": exit_code}
