from mcp.server.fastmcp import FastMCP
import logging
from tools.docker_runner import run_isolated_test
from tools.ast_auditor import validate_patch_syntax
from tools.github_client import GitHubClient

logger = logging.getLogger(__name__)

# Initialize the FastMCP 2.0 Server Registry
mcp = FastMCP("GhostMachine SRE Tools")

@mcp.tool()
def ping_target_system() -> str:
    """Diagnostic tool to verify the MCP server is actively bound to the host."""
    logger.info("Ping tool invoked.")
    return "GhostMachine MCP Server Online. Host execution authorized."

@mcp.tool()
def sandbox_test(test_path: str, repo_path: str) -> dict:
    """Executes a test file inside an ephemeral Docker sandbox."""
    result = run_isolated_test(test_path, repo_path)
    return {"exit_code": result.exit_code, "stdout": result.stdout, "stderr": result.stderr}

@mcp.tool()
def audit_syntax(source_code: str) -> list[str]:
    """Validates patch code against security guardrails."""
    return validate_patch_syntax(source_code)

@mcp.tool()
async def stage_pr(repo: str, branch: str, title: str, body: str, diff: str, token: str) -> dict:
    """Opens a GitHub PR with the validated patch."""
    client = GitHubClient(repo=repo)
    try:
        result = await client.create_pull_request(title=title, head_branch=branch, base_branch="main", body=body)
        return {"pr_url": result.get("html_url"), "status": "created"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}
    finally:
        await client.close()
