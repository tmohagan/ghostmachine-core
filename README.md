# GhostMachine

> **SYSTEM.STATUS: ONLINE**<br>
> INITIALIZING GHOSTMACHINE CORE...<br>
> AUTONOMOUS SRE AGENT ENGAGED.<br>
> FAULT DETECTION ACTIVE.<br>
> AI REMEDIATION PIPELINE READY.<br>

[**ghostmachine.dev**](https://ghostmachine.dev)

GhostMachine is an autonomous Site Reliability Engineering (SRE) system designed to detect, diagnose, and remediate faults in real-time. Utilizing advanced language models, it generates and tests patches before automatically submitting pull requests to ensure system uptime and stability.

## Overview

Modern infrastructure is complex, and diagnosing unexpected production faults takes time. GhostMachine acts as an AI-driven control plane that continuously listens for system faults (e.g., from an attached application like the [Tim O'Hagan CMS](https://github.com/tmohagan/tim-ohagan-cms)). When an exception occurs:
1. **Detection**: The control plane receives a webhook containing the error trace.
2. **Analysis**: An adversarial fuzzer and LLM orchestration layer diagnose the root cause of the fault.
3. **Remediation**: GhostMachine synthesizes a patch to resolve the issue.
4. **Resolution**: A Pull Request is automatically generated and submitted to the target repository.

## Components

- **Control Plane**: A FastAPI application that acts as the ingress for webhooks and coordinates the SRE tasks.
- **Chaos Harness**: Adversarial fuzzing and evaluation nodes to test and validate patches.
- **Orchestrator**: Nodes dedicated to prompting language models to synthesize code patches.
- **Ingress Proxy**: Caddy server configured for automatic TLS provisioning and traffic routing.

## Technology Stack

- **Framework**: FastAPI (Python 3.11)
- **AI/LLM**: Google Gemini (via `google-genai` SDK)
- **Ingress**: Caddy (Dockerized)
- **Orchestration**: Docker Compose

## Setup and Deployment

GhostMachine is designed to be deployed alongside its target applications.

1. Clone the repository:
   ```bash
   git clone https://github.com/tmohagan/ghostmachine-core.git
   cd ghostmachine-core
   ```
2. Configure your environment variables in a `.env` file (e.g., `GEMINI_API_KEY`, GitHub credentials).
3. Start the system:
   ```bash
   docker network create ghostmachine-bridge
   docker compose -f compose.yaml -f compose.proxy.yaml up -d --build
   ```

## Reference Target

GhostMachine is designed to monitor and remediate the [Tim O'Hagan CMS](https://github.com/tmohagan/tim-ohagan-cms). The CMS includes a dedicated chaos playground for fault injection testing.

## License

MIT License
