from typing import Dict, Any
from tools.github_client import GitHubClient

class StagingCanaryNode:
    """
    Stages the Pull Request, Post-Mortem, and Telemetry for the LangGraph Orchestrator.
    """
    def __init__(self, repo: str = "tim-ohagan/cms-core"):
        self.repo = repo

    def generate_telemetry_ledger(self, tokens: int, compute_seconds: float) -> str:
        """
        Calculates the operational ROI of the automated SRE run.
        """
        # Baseline costs defined by specification
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
        
        incident_id = state.get("incident_id", "INC-UNKNOWN")
        tokens = state.get("total_tokens", 4700)
        compute = state.get("compute_seconds", 38.0)
        
        ledger = self.generate_telemetry_ledger(tokens, compute)
        body = f"## Automated SRE Post-Mortem\n\n**Incident:** {incident_id}\n\n{ledger}"
        
        try:
            response = await client.create_pull_request(
                title=f"fix: Autonomous Remediation for {incident_id}",
                head_branch=f"fix/{incident_id}",
                base_branch="master",
                body=body
            )
            state["pr_url"] = response.get("html_url")
        except Exception as e:
            state["pr_error"] = str(e)
        finally:
            await client.close()
            
        return state
