import os
import httpx
from typing import Dict, Any

class GitHubClient:
    """
    Manages TCP socket connections to the GitHub REST API.
    Maintains an asynchronous connection pool to reuse TLS sessions.
    """
    def __init__(self, repo: str):
        self.token = os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is missing.")
            
        self.repo = repo
        self.client = httpx.AsyncClient(
            base_url=f"https://api.github.com/repos/{self.repo}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28"
            },
            timeout=10.0
        )

    async def create_pull_request(self, title: str, head_branch: str, base_branch: str, body: str) -> Dict[str, Any]:
        """
        Serializes a JSON payload and transmits it over the TCP socket to 
        the GitHub REST API to propose a branch merge.
        """
        payload = {
            "title": title,
            "head": head_branch,
            "base": base_branch,
            "body": body
        }
        
        response = await self.client.post("/pulls", json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self):
        """
        Explicitly close the TCP sockets and release the file descriptors.
        """
        await self.client.aclose()
