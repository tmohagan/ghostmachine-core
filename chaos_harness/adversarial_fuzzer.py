import os
import httpx
import asyncio
import sys

async def trigger_chaos_fault():
    """
    Transmits an HTTP request to the target's chaos playground endpoint 
    to intentionally trigger a 500 CPU fault for SRE evaluation.
    """
    target = os.environ.get("TARGET_URL", "http://tim-ohagan.local").rstrip("/")
    url = target if "/playground/fault/500" in target else f"{target}/playground/fault/500"
    
    print(f"Triggering chaos fault at {url}...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=5.0)
            print(f"Target responded with HTTP {response.status_code}")
            if response.status_code >= 500:
                print("Success: 5xx Exception triggered.")
        except Exception as e:
            print(f"Socket connection failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(trigger_chaos_fault())
