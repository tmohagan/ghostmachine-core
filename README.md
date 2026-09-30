# GhostMachine SRE Control Plane

[![Live Production](https://img.shields.io/badge/Live-ghostmachine.dev-00ffff?style=flat-square)](https://ghostmachine.dev)
[![Target CMS](https://img.shields.io/badge/Target-tim--ohagan.com-38bdf8?style=flat-square)](https://tim-ohagan.com)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-orange?style=flat-square)](https://github.com/langchain-ai/langgraph)
[![Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-8e24aa?style=flat-square)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/Sandbox-Docker-2496ed?style=flat-square)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

> **SYSTEM.STATUS: ONLINE**<br>
> CENTRAL OPERATING SYSTEM (COS) ACTIVE.<br>
> OPENTELEMETRY INGESTION ENGAGED.<br>
> AST STATIC GUARDRAILS ACTIVE.<br>
> AUTONOMOUS REMEDIATION PIPELINE READY.

[**ghostmachine.dev**](https://ghostmachine.dev) is an autonomous Site Reliability Engineering (SRE) control plane. When connected target applications encounter production faults, GhostMachine ingests the error trace, synthesizes an isolated reproduction test, drafts a code fix via language models, audits the patch against compiler-level AST guardrails, verifies it in an ephemeral sandbox, and submits a pull request with an economic post-mortem in under 90 seconds.

---

## Live Endpoints

- **Production URL**: [https://ghostmachine.dev](https://ghostmachine.dev) (Canonical)
- **Subdomain**: [https://www.ghostmachine.dev](https://www.ghostmachine.dev) (Automated 301 Redirect)
- **Interactive COS Uplink**: [https://ghostmachine.dev/#uplink](https://ghostmachine.dev/#uplink)
- **Remediation Pipeline**: [https://ghostmachine.dev/#pipeline](https://ghostmachine.dev/#pipeline)
- **Live Chaos Trigger**: [https://ghostmachine.dev/#demo](https://ghostmachine.dev/#demo) -> [tim-ohagan.com/#playground](https://tim-ohagan.com/#playground)

---

## Remediation Workflow (LangGraph State Machine)

```
[ Ingest Span ] ──▶ [ Repro Test ] ──▶ [ Ephemeral Sandbox ] ──▶ [ Patch Synthesis ] ──▶ [ AST Guardrails ] ──▶ [ Sandbox Final ] ──▶ [ GitHub PR ]
```

1. **Ingest Span**: Intercepts 5xx fault webhooks and parses stack frames, request vectors, and OpenTelemetry trace context. Implements a Redis trace hashing deduplication layer (SHA-256 of top 5 stack frames) to prevent container exhaustion during cascading outages by enforcing a 15-minute TTL on identical signatures.
2. **Repro Test Synthesis**: Generates a standalone `pytest` test case replicating the exact crash condition using `httpx`, dynamically resolving endpoint routes and operations from OpenAPI specifications.
3. **Sandbox Execution**: Executes the reproduction test inside an isolated Docker container with strict compute and memory constraints. Patches are applied leniently via `patch -p1` with Docker volume `safe.directory` handling. The test must fail (`exit_code != 0`) to confirm bug reproducibility.
4. **Patch Synthesis & AST Guardrails**:
   - Uses **Lightweight Context Enrichment** to dynamically resolve traceback lines to local host files, extracting +/- 15 lines of source code context around the crash site to inject into the LLM prompt.
   - Generates minimal unified git diffs (capped at 80 lines).
   - Validates **modified files** against Python's native `ast` compiler: detects bare `except:` blocks, restricts dangerous system primitives (`os.system`, `subprocess`, `eval`), and enforces zero-trust code generation.
   - If the guardrail blocks the patch, the workflow conditionally loops back to patch synthesis (up to 3 retries) to self-correct.
5. **Regression Verification (Sandbox Final)**: Runs both reproduction tests and the site's full regression test suite inside the patched container (`exit_code == 0`). If tests fail, conditionally loops back to patch synthesis (up to 3 retries) for true functional self-correction.
6. **Canary Staging & PR Submission**: 
   - A hard gate ensures no code touches GitHub unless `guardrail_status == "passed"`.
   - Bypasses Docker volume "dubious ownership" boundaries (`git config --global --add safe.directory`).
   - Applies the generated patch leniently via `patch -p1`.
   - Force-adds the reproduction test case to guarantee a non-empty PR payload, preventing GitHub 422 errors.
   - Opens a validated GitHub Pull Request containing an automated SRE Post-Mortem and an Economic Telemetry Ledger comparing automation cost (~$0.026) vs manual engineering baseline (~$42.50).

---

## Control Plane & Components

- **Control Plane API (`control_plane/`)**: FastAPI server providing webhook ingestion and health checks (`GET /health` direct, `GET /api/health` reverse-proxied via Caddy).
- **Webhook Ingestion (`POST /api/webhooks`)**: Protected with timing-attack resistant shared secret verification (`X-GhostMachine-Secret`).
- **COS Uplink AI (`POST /api/cos/chat`)**: Interactive persona chatbot powered by Google Gemini (`gemini-3.8-flash`) simulating the Central Operating System.
- **Orchestrator (`orchestrator/`)**: Typed `LangGraph` StateGraph coordinating node state across ingestion, reproduction, patching, and staging. The shared `IncidentState` TypedDict declares 18 fields covering trace context, patch content, guardrail results, PR output, telemetry costs, and post-mortem metadata.
- **Caddy Ingress Proxy (`Caddyfile`)**: Production reverse proxy with automatic Let's Encrypt certificates for apex and `www.` domains, modern Zstandard/Gzip compression, and hardened security headers (`HSTS`, `nosniff`, `SAMEORIGIN`).

---

## Environment Variables

| Variable | Description |
| :--- | :--- |
| `GEMINI_API_KEY` | Google AI Studio API Key for patch synthesis and COS chat |
| `GITHUB_TOKEN` | GitHub Personal Access Token for creating remediation branches and PRs |
| `GITHUB_REPO` | Target repository identifier (e.g., `tmohagan/tim-ohagan-cms`) |
| `CMS_REPO_PATH` | Path to target codebase on disk or mounted container volume |
| `WEBHOOK_SECRET` | Shared secret key required on `POST /api/webhooks` |
| `REDIS_URL` | Connection string for Redis instance used in alert deduplication |

---

## Setup and Deployment

### 1. Configure Environment
Create a `.env` file in the project root:
```ini
GEMINI_API_KEY=your_gemini_api_key
GITHUB_TOKEN=your_github_token
GITHUB_REPO=tmohagan/tim-ohagan-cms
CMS_REPO_PATH=/opt/ghostmachine/tim-ohagan-cms
WEBHOOK_SECRET=your_super_secret_webhook_key
REDIS_URL=redis://localhost:6379/0
```

### 2. Launch with Docker Compose
```bash
# Create shared bridge network
docker network create ghostmachine-bridge

# Build and start control plane and Caddy ingress
docker compose -f compose.yaml -f compose.proxy.yaml up -d --build
```

---

## Reference Target

GhostMachine actively monitors [tim-ohagan.com](https://tim-ohagan.com) (repo: [tim-ohagan-cms](https://github.com/tmohagan/tim-ohagan-cms)). Trigger live failure vectors in the [Chaos Playground](https://tim-ohagan.com/#playground) to witness real-time fault detection and PR synthesis.

---

## License

MIT License. Developed by [Tim O'Hagan](https://github.com/tmohagan).
