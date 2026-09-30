# GhostMachine & CMS Ecosystem: Project Knowledge Base

This Knowledge Base serves as the central reference for developers and operators working with the **GhostMachine SRE Control Plane** and **Tim O'Hagan CMS**.

---

## 1. Quick Links & References

### Code Repositories
*   **CMS / Target App**: `github.com/tmohagan/tim-ohagan-cms`
*   **SRE Control Plane**: `github.com/tmohagan/ghostmachine-core`

### Live Environments
*   **CMS Production**: [https://tim-ohagan.com](https://tim-ohagan.com)
*   **Chaos Playground**: [https://tim-ohagan.com/#playground](https://tim-ohagan.com/#playground)
*   **SRE Control Plane**: [https://ghostmachine.dev](https://ghostmachine.dev)

### Architecture
*   [System Architecture & Context Document](./system_architecture.md)

---

## 2. Environment & Secrets Management

The entire stack is hosted on a single GCP VM (`ghostmachine-vm`). Secrets are managed via `.env` files and Docker environment variables.

### Required Secrets (`.env`)
| Variable | Component | Purpose |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Control Plane | Authenticate with Google AI Studio for LLM patch generation. |
| `GITHUB_TOKEN` | Control Plane | Push branches and open PRs on the target repository. |
| `GITHUB_REPO` | Control Plane | Target repository identifier (e.g., `tmohagan/tim-ohagan-cms`). |
| `CMS_REPO_PATH` | Control Plane | Absolute path to the target codebase on disk or mounted volume. |
| `WEBHOOK_SECRET` | Both | Shared cryptographic secret used to sign telemetry payloads. |
| `REDIS_URL` | Control Plane | Connection string for the Redis deduplication layer (`redis://redis:6379/0`). |
| `GHOSTMACHINE_WEBHOOK_URL` | CMS | Outbound telemetry endpoint on the control plane (e.g., `http://control-plane:8000/api/webhooks`). |
| `DATABASE_URL` | CMS | `postgresql+asyncpg://...` connection string. |
| `POSTGRES_PASSWORD` | Control Plane | Secure password for the `ghostmachine-postgres` database. |
| `DATABASE_URL` | Control Plane | Connection string for `ghostmachine-postgres` to support LangGraph checkpointing (e.g., `postgresql://ghostmachine:your_password_here@postgres:5432/ghostmachine_db`). |
| `ADMIN_USERNAME` | CMS | Basic Auth username (default: `admin`). |
| `ADMIN_PASSWORD` | CMS | Basic Auth password for contact inbox access. |

> **Security Note**: The `WEBHOOK_SECRET` is used by the CMS `GhostMachineMiddleware` to sign payloads sent to the SRE Control Plane. The Control Plane verifies this using constant-time string hashing (`secrets.compare_digest`).

---

## 3. Developer Workflow

### Local Development (CMS)
```bash
cd tim-ohagan-cms

# Start local services (Postgres, Redis, FastAPI)
docker compose up --build -d

# Run database migrations
poetry run alembic upgrade head

# Run tests
poetry run pytest -v
```

### Local Development (GhostMachine Control Plane)
```bash
cd ghostmachine-core

# Create shared network (required for bridging with CMS)
docker network create ghostmachine-bridge

# Start control plane
docker compose -f compose.yaml -f compose.proxy.yaml up -d --build

# Verify service health endpoints through Caddy proxy
curl -k https://tim-ohagan.local/health
curl -k https://ghostmachine.local/api/health
```

---

## 4. Troubleshooting & Runbooks

### 4.1. Webhooks Failing to Trigger Remediation
**Symptoms**: The CMS throws an error (e.g., from the Chaos Playground), but no PR is generated.
**Diagnosis Steps**:
1. Check CMS logs to ensure the middleware intercepted the error:
   `docker logs cms-app`
2. Check Control Plane ingestion logs:
   `docker logs control-plane`
3. Verify the `WEBHOOK_SECRET` perfectly matches between both `.env` files.
4. Verify the `GHOSTMACHINE_WEBHOOK_URL` in the CMS environment points to the correct internal Docker bridge IP or public endpoint.

### 4.2. Sandbox Execution Failing (False Negatives)
**Symptoms**: The LLM generates a patch, but the regression verification fails even though the fix appears correct.
**Diagnosis Steps**:
1. Inspect the LangGraph node output for the `SandboxExecution` state.
2. Verify that `docker` limits (memory/CPU) are not causing unrelated OOM kills during test execution.
3. Check `orchestrator/nodes/sandbox.py` to ensure the generated `pytest` file is correctly mounted and execution paths align with the container workspace.

### 4.3. Git Commands Failing in Docker ("Dubious Ownership")
**Symptoms**: Git commands in the staging node fail with `fatal: detected dubious ownership in repository`.
**Diagnosis Steps**:
1. This is a security feature triggered when Docker mounts host volumes with differing user IDs.
2. The pipeline now resolves this automatically by injecting `git config --global --add safe.directory <repo_path>` before executing git commands. This is applied in both `staging_canary_node` (for PR creation) and `sandbox_execution_node` (for patch application during regression testing).

### 4.4. GitHub PR Creation Fails (422 Unprocessable Entity)
**Symptoms**: The git branch is pushed successfully, but the GitHub API throws a 422 error when opening the Pull Request.
**Diagnosis Steps**:
1. A 422 error here almost always means the underlying commit was empty (i.e., the branch is identical to `main`).
2. This happens if the LLM patch failed to apply via `patch -p1` and no other files were staged.
3. The pipeline now force-adds the reproduction test case (`git add -f tests/...`) to ensure the PR always contains a diff, bypassing this error. Ensure `.gitignore` rules do not override the force-add.

### 4.5. Caddy Ingress SSL Errors
**Symptoms**: Browsers report invalid certificates for `tim-ohagan.com` or `ghostmachine.dev`.
**Diagnosis Steps**:
1. View Caddy logs: `docker logs ghostmachine-ingress`
2. Verify DNS A records point to the correct VM public IP.
3. Ensure port `80` and `443` are open on the GCP firewall to allow Let's Encrypt HTTP-01 challenges.

### 4.6. Gemini API Credit Exhaustion (402 RESOURCE_EXHAUSTED)
**Symptoms**: The pipeline ingests the fault and reaches the `repro` node, but fails with `google.genai.errors.ClientError: 402 RESOURCE_EXHAUSTED`.
**Diagnosis Steps**:
1. This means your Google AI Studio prepaid credits are depleted.
2. Visit [AI Studio](https://ai.studio/projects) to top up credits or switch to a billing-enabled project.
3. The pipeline infrastructure itself is fully operational — no code changes needed. Once credits are restored, the next fault injection will produce a PR.

### 4.7. Alembic Database Migration Desync / Missing Revision
**Symptoms**: Running `alembic current` or `alembic upgrade head` errors with `Can't locate revision identified by '<revision_id>'`. The `contact_messages` table or other newer schema changes may be missing from the database.
**Diagnosis Steps**:
1. Inspect the revision stored in the database:
   `docker exec cms-postgres psql -U cms_user -d cms_db -c "SELECT * FROM alembic_version;"`
2. Compare the database revision against the actual migration chain in `tim-ohagan-cms/alembic/versions/`:
   `ls -la tim-ohagan-cms/alembic/versions/`
3. If the database points to a deleted or non-existent revision hash, reset the pointer to the latest known valid revision:
   `docker exec cms-postgres psql -U cms_user -d cms_db -c "UPDATE alembic_version SET version_num = '106fe860d751';"`
4. Run the migration to bring the schema to current head:
   `docker exec cms-app poetry run alembic upgrade head`
5. Verify the tables (`alembic_version`, `profiles`, `posts`, `contact_messages`):
   `docker exec cms-postgres psql -U cms_user -d cms_db -c "\dt"`

---

## 5. Deployment Runbook

Updates to production are handled via standard Git pull and Docker container recreation on the VM.

```bash
# 1. SSH into the production VM
gcloud compute ssh ghostmachine-vm --project=ghostmachine --zone=<zone>

# 2. Pull latest code (CMS Example)
cd /home/tim/workspace/tim-ohagan-cms
git pull origin main

# 3. Rebuild and restart the application
docker compose up --build -d app

# 4. Prune unused images to save disk space
docker image prune -f
```

---

## 6. SRE AI Orchestration Summary

The LangGraph State Machine manages the remediation lifecycle via 7 nodes in a linear graph with conditional loops. State persistence is managed by a **PostgresSaver checkpointer** using a dedicated `ghostmachine-postgres` container. This ensures the orchestrator survives container restarts and transient API failures, allowing the pipeline to resume from the last successful node. If modifying the orchestrator workflow, note the following nodes in `ghostmachine-core/orchestrator/`:

*   **Ingest Node** (`ingest`): Extracts trace IDs, validates schema, applies Redis trace hashing (SHA-256 of exception class and top frames) to drop duplicate alerts within a 15-minute window, and writes to the append-only audit log.
*   **Repro Node** (`repro`): Sends the stack trace to `gemini-3.8-flash` and compiles a pure Python `httpx` test to reproduce the crash.
*   **Sandbox Node** (`sandbox_initial`): Spins up an ephemeral Docker container running on the secure **gVisor (`runsc`)** runtime, applies any existing patch via `patch -p1`, and runs the repro test. Asserts `exit_code != 0`.
*   **Patch Node** (`patch`): Employs **Local Context Enrichment** to extract source code snippets from the target files based on the stack trace. Sends the enriched prompt (failing test, stack trace, and local code context) to `gemini-3.8-flash` to generate a minimal unified git diff. Includes context from previous failed validation/test attempts.
*   **Guardrails Node** (`guardrail`): Copies the repo to a temp directory, applies the patch via `patch -p1`, and walks the AST of **only the modified files** to block bare `except:` blocks and dangerous execution primitives (`os.system`, `subprocess`, `eval`). Features conditional routing back to the `patch` node (up to 3 times) if the patch violates guardrails.
*   **Sandbox Final Node** (`sandbox_final`): Evaluates the functional correctness of the patch and checks for regressions. Runs both the repro test and the full regression test suite inside an ephemeral Docker container using the **gVisor (`runsc`)** runtime. If the test fails (`exit_code != 0`), it conditionally loops back to the `patch` node (up to 3 times) for functional self-correction. If it passes, it proceeds to staging.
*   **Stage Node** (`stage`): Acts as a final hard gate checking that `guardrail_status == "passed"`. Writes the post-mortem report, applies the patch to the CMS repo via `patch -p1`, commits, pushes, and opens a GitHub PR via the async `GitHubClient`.
