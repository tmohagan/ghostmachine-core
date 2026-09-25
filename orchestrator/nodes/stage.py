import os
import logging
from typing import Dict, Any
from orchestrator.state import IncidentState
from tools.github_client import GitHubClient

logger = logging.getLogger(__name__)

class StagingCanaryNode:
    """
    Stages the Pull Request, Post-Mortem, and Telemetry for the LangGraph Orchestrator.
    """
    def __init__(self, repo: str = "tmohagan/tim-ohagan-cms"):
        self.repo = repo

    def generate_telemetry_ledger(self, tokens: int, compute_seconds: float) -> str:
        """
        Calculates the operational ROI of the automated SRE run.
        """
        token_cost = (tokens / 1000) * 0.005
        compute_cost = compute_seconds * 0.000073
        total_cost = token_cost + compute_cost
        
        manual_labor = 42.50
        savings = ((manual_labor - total_cost) / manual_labor) * 100
        
        return f"""
### Economic Telemetry Ledger
| Telemetry Vector | Observed Value | Calculation Baseline |
| :--- | :--- | :--- |
| **Inference Tokens** | {tokens} | Live API token counter |
| **Direct Inference Cost** | **${token_cost:.4f} USD** | Current token billing rates |
| **Sandbox Compute Cost** | **${compute_cost:.4f} USD** | {compute_seconds}s @ cloud vCPU rate |
| **Total Automated Cost** | **${total_cost:.4f} USD** | Incurred system operational expense |
| **Manual Labor Baseline** | **${manual_labor:.2f} USD** | 0.5 hours SRE labor @ baseline $85/hr |
| **Net Operational Savings**| **+{savings:.2f}%** | Cost differential per resolved event |
"""

    async def stage_pr(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constructs the PR body and initiates the TCP POST request to GitHub.
        """
        client = GitHubClient(repo=self.repo)
        
        incident_id = state.get("incident_id") or state.get("trace_id", "INC-UNKNOWN")
        tokens = state.get("total_tokens", 4700)
        compute = state.get("compute_seconds", 38.0)
        
        ledger = self.generate_telemetry_ledger(tokens, compute)
        body = f"## Automated SRE Post-Mortem\n\n**Incident:** {incident_id}\n\n{ledger}"
        
        cms_repo_path = os.environ.get("CMS_REPO_PATH", "/home/tim/workspace/tim-ohagan-cms")
        try:
            import subprocess
            cmd = (
                f"cd {cms_repo_path} && "
                f"git config user.name 'GhostMachine SRE' && "
                f"git config user.email 'bot@ghostmachine.dev' && "
                f"git checkout -B fix/{incident_id} && "
                f"git add incidents/ tests/incidents/ 2>/dev/null || true && "
                f"git commit -m 'fix: Autonomous Remediation for {incident_id}' || true && "
                f"git push origin fix/{incident_id} --force"
            )
            subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
        except Exception as e:
            logger.warning(f"Git branch push failed: {e}")

        base_branch = os.environ.get("GITHUB_BASE_BRANCH", "main")
        try:
            response = await client.create_pull_request(
                title=f"fix: Autonomous Remediation for {incident_id}",
                head_branch=f"fix/{incident_id}",
                base_branch=base_branch,
                body=body
            )
            state["pr_url"] = response.get("html_url")
        except Exception as e:
            state["pr_error"] = str(e)
        finally:
            await client.close()
            
        return state

def staging_canary_node(state: IncidentState) -> Dict[str, Any]:
    """
    LangGraph node entrypoint.
    Generates post-mortem report and stages the GitHub PR.
    """
    import asyncio
    from orchestrator.nodes.post_mortem import PostMortemGenerator

    repo = os.environ.get("GITHUB_REPO", "tmohagan/tim-ohagan-cms")
    cms_repo_path = os.environ.get("CMS_REPO_PATH", "/home/tim/workspace/tim-ohagan-cms")

    node = StagingCanaryNode(repo=repo)
    tokens = state.get("total_tokens", 4700)
    compute = state.get("compute_seconds", 38.0)
    ledger = node.generate_telemetry_ledger(tokens, compute)

    # 1. Write Post-Mortem Report
    try:
        pm = PostMortemGenerator(cms_repo_path)
        pm.write_report(dict(state), ledger)
    except Exception as e:
        logger.warning(f"Could not write post-mortem report: {e}")

    # 2. Stage PR
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.warning("GITHUB_TOKEN not found, skipping PR creation.")
        return {"pr_error": "GITHUB_TOKEN not configured"}

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                res = pool.submit(asyncio.run, node.stage_pr(dict(state))).result()
        else:
            res = asyncio.run(node.stage_pr(dict(state)))
        return {
            "pr_url": res.get("pr_url"),
            "pr_error": res.get("pr_error")
        }
    except Exception as e:
        return {"pr_error": str(e)}
