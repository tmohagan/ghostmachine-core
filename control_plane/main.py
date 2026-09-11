from fastapi import FastAPI
from control_plane.api.webhooks import router as webhooks_router

app = FastAPI(
    title="GhostMachine SRE Control Plane",
    description="Autonomous remediation orchestrator and FastMCP host.",
    version="1.0.0"
)

# Mount the physical ingestion router to the application context
app.include_router(webhooks_router)

@app.get("/health")
async def health_check():
    """Diagnostic endpoint to verify socket connectivity."""
    return {"status": "online", "service": "ghostmachine-core"}
