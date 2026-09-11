import os
from typing import Dict, Any

class PostMortemGenerator:
    """
    Synthesizes LangGraph trace state into a structured Markdown document 
    and flushes the bytes to the physical local filesystem.
    """
    def __init__(self, target_repo_path: str):
        self.target_repo_path = target_repo_path

    def write_report(self, state: Dict[str, Any], ledger_text: str) -> str:
        """
        Executes File I/O to create the incident report on disk.
        """
        incident_id = state.get("incident_id", "INC-UNKNOWN")
        
        # 1. Issue syscall to create directory if missing
        incidents_dir = os.path.join(self.target_repo_path, "incidents")
        os.makedirs(incidents_dir, exist_ok=True)
        
        file_path = os.path.join(incidents_dir, f"{incident_id}.md")
        
        # 2. Construct the byte payload based on spec requirements
        content = f"""# Automated SRE Post-Mortem: {incident_id}

## Incident Summary
* **Root Cause Analysis:** {state.get("root_cause", "Pending Analysis")}
* **Affected Endpoints:** {state.get("affected_endpoints", "Unknown")}
* **Total Downtime:** {state.get("downtime_ms", 0)} ms

## High-Resolution Timeline
* **Trace Ingested:** {state.get("timestamp_ingest", "N/A")}
* **Patch Generated:** {state.get("timestamp_patch", "N/A")}
* **Tests Passed:** {state.get("timestamp_success", "N/A")}

## 5 Whys Analysis
{state.get("five_whys", "Analysis pending.")}

## Preventative Recommendations
{state.get("recommendations", "None provided.")}

{ledger_text}
"""
        
        # 3. Open a file descriptor and flush bytes to physical storage
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return file_path
