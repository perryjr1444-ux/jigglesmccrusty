# Mac Blue-Team Framework

A modular framework that orchestrates blue-team remediation workflows on macOS environments. It exposes a FastAPI service that accepts incident cases, runs policy-guarded playbooks, and records tamper-evident audit logs while delegating remediation work to specialised agent modules and external service connectors.

## Project Layout

```
mac-blue-team-framework/
├─ api/                    # Public HTTP API (FastAPI)
│   ├─ main.py             # FastAPI entry point
│   └─ routes.py           # Endpoints: ingest case, approve task, fetch audit
├─ agents/                 # "LLM agents" – pure Python functions, no model inside
│   ├─ commander.py        # builds the DAG from a playbook definition
│   ├─ identity_locker.py  # password-rotation, 2FA enrollment, token prune
│   ├─ device_remediator.py
│   ├─ network_steward.py
│   ├─ evidence_clerk.py
│   ├─ platform_reporter.py
│   └─ hardening_coach.py
├─ connectors/             # thin wrappers around external services
│   ├─ gmail.py            # Google Workspace / Gmail admin SDK
│   ├─ msgraph.py          # Microsoft Graph
│   ├─ router.py           # vendor-agnostic router reset (UPnP/CLI)
│   ├─ carrier.py          # carrier-port-out lock helpers
│   └─ vault.py            # envelope-encrypt secrets (AWS KMS/HSM)
├─ core/                   # orchestration engine
│   ├─ dag.py              # lightweight DAG implementation
│   ├─ orchestrator.py     # state-machine that drives tasks
│   ├─ policy.py           # OPA-style guardrails (Python DSL)
│   ├─ audit.py            # tamper-evident append-only log (Merkle-tree)
│   └─ models.py           # Pydantic schemas for Case/Task/Artifact
├─ playbooks/              # YAML definitions of response flows
├─ utils/                  # helpers (redaction, tokenisation, hashing)
├─ scripts/                # dev / deployment helpers
├─ Dockerfile              # container image (Python 3.12, uvicorn, gunicorn)
├─ docker-compose.yml      # Postgres, MinIO, Vault, API
└─ pyproject.toml          # Poetry dependencies
```

## Quickstart

1. Install dependencies:

   ```bash
   poetry install
   ```

2. Generate local secrets and bootstrap supporting services:

   ```bash
   ./scripts/bootstrap.sh
   ```

3. Launch the full stack with Docker Compose:

   ```bash
   ./scripts/run_local.sh
   ```

4. Submit a case to the API:

   ```bash
   curl -X POST http://localhost:8080/cases \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Suspicious mailbox forwarding",
       "description": "Auto-forward to unknown address",
       "playbook": "email_takeover_v1"
     }'
   ```

5. Review task approvals and audit entries via the API:

   ```bash
   curl http://localhost:8080/audit
   ```

## Development Notes

- Agent modules are deterministic, dependency-free functions that produce structured outputs to keep prompts and model coupling outside of the repository.
- Policy guardrails execute before each task to prevent unsafe actions and guarantee that approvals are recorded.
- The audit log builds a Merkle tree so that log tampering is detectable by recomputing hashes offline.
- Playbooks are YAML DAG definitions that the commander converts into executable tasks at runtime.

## License

Licensed under the MIT License. See [LICENSE](LICENSE).
