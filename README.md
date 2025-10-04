# AI-Augmented SOC: Modular LLM Architecture

This document captures a modular, hierarchical LLM-powered architecture that extends the previously discussed AI-augmented SOC design. The system separates the three classic cyber-security teams—Red, Blue, and Purple—into specialised LLM suites orchestrated by a lightweight task router.

## 1. High-Level Diagram
```
+----------------------+      +----------------------+      +----------------------+
|   Red Team LLMs      | ---> |   Orchestration Hub  | <--- |   Blue Team LLMs    |
| (Attack-gen, Phishing,|      | (task router, queue, |      | (Alert-enrich,      |
|  Malware-craft)      |      |  policy engine)      |      |  Incident-playbooks)|
+----------------------+      +----------------------+      +----------------------+
                                 ^          |
                                 |          v
                         +---------------------------+
                         |   Purple Team LLM (Meta)  |
                         |  (Gap analysis, metric    |
                         |   synthesis, model update)|
                         +---------------------------+
```

All LLM suites read from and write to the central SIEM (Elastic/OpenSearch) and trigger SOAR playbooks via the orchestration hub. Each box represents one or more containerised LLM instances that can be swapped or scaled independently.

## 2. Component Breakdown

### 2.1 Red-Team LLM Suite

| Instance           | Core Prompt / Role                                                                                     | Typical Output                                                                                                     | Integration Point                                          |
|--------------------|--------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| **Red-Gen**        | "You are a skilled penetration tester. Generate a realistic multi-stage attack against a macOS endpoint, using publicly known exploits and custom payloads." | Attack playbook, malicious binaries (base64), phishing collateral, C2 configuration.                                | Writes `red-scenarios-*` documents in the SIEM.            |
| **Phish-LLM**      | "Compose a convincing spear-phishing email targeting a senior engineer, embedding a malicious link."  | Email body, subject line, encoded attachment.                                                                       | Augments scenarios with social-engineering vectors.        |
| **Malware-Craft**  | "Produce a small macOS-compatible payload (Swift/Python) that exfiltrates `/Users/*/Documents` to a given C2 URL." | Source code, compile commands, payload hash.                                                                         | Stores artifacts linked to the scenario.                   |
| **Adversary-Emulation** | "Translate MITRE ATT&CK technique T1059 (Command-Shell) into a macOS Bash one-liner usable in the scenario." | Command snippets, expected telemetry.                                                                               | Supports Blue-LLM detection generation.                    |

**Deployment tip:** Run each instance in lightweight Docker/Podman containers on macOS using quantised models (e.g., Llama-3-8B-Chat-Q4_K_M). Quantisation reduces RAM to roughly 6 GB per container, allowing two to three instances on a modern M2 Max MacBook Pro.

### 2.2 Blue-Team LLM Suite

| Instance              | Core Prompt / Role                                                                                               | Typical Output                                                                 | Integration Point                                              |
|-----------------------|------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|-----------------------------------------------------------------|
| **Alert-Enricher**    | "Given the raw OSQuery process log below, identify whether it matches any known malicious behaviours from the attached red scenario." | Enriched alert JSON (`ml.red_match=true`, ATT&CK mapping).                     | Updates `alerts-*` documents in the SIEM.                      |
| **Detection-Builder** | "From the red-scenario describing a PowerShell-like macOS script, synthesise a Sigma rule that detects its execution pattern." | Sigma/YAML detection rules mapped to Elastic/Kibana.                           | Auto-loads into the SIEM detection engine.                    |
| **Playbook-Executor** | "If an alert with `ml.red_match=true` appears, generate a containment playbook (isolate device, kill process, collect memory dump)." | SOAR-compatible playbook JSON.                                                | Sent to SOAR platforms via webhook.                           |
| **Forensic-Analyst**  | "Summarise the timeline of events from the SIEM for host Mac-1234 after the red scenario triggered."             | Narrative timeline, evidence list, recommended artefacts.                      | Attached to incident tickets.                                 |

**Deployment tip:** Operate Blue-LLMs with a larger reasoning model (e.g., Mistral-7B-Instruct-v0.2) accelerated via `llama.cpp` + Metal on Apple Silicon.

### 2.3 Purple-Team LLM Suite

| Instance                | Core Prompt / Role                                                                                                     | Typical Output                                                 | Integration Point                        |
|-------------------------|------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------|-------------------------------------------|
| **Gap-Analyzer**        | "Compare the red-scenario steps with the blue-team detection coverage. List any ATT&CK techniques that were not detected." | Gap report JSON with severity scores.                         | Writes to `purple-gaps-*` index.          |
| **Metric-Synthesiser**  | "From the last 30 days of red-scenario executions and blue responses, compute detection-rate, MTTD, and MTTC."           | KPI dashboard JSON.                                            | Drives executive reporting dashboards.     |
| **Model-Updater**       | "Based on the gap report, suggest a new prompt tweak for the Red-Gen LLM and a new rule tweak for the Blue-Alert-Enricher." | Updated prompt strings, version metadata.                     | Triggers CI/CD container redeployments.    |
| **Adversary-Defender Dialogue** | "Simulate a conversation where the Red-LLM tries to bypass the newly added detection rule and the Blue-LLM counters." | Dialogue transcript for analyst training.                     | Optional enrichment material.              |

**Deployment tip:** Purple-team tasks can leverage compact summarisation models (e.g., Phi-2-7B) because their inputs are already structured.

## 3. Orchestration Hub (Task Router)

A slim Python or Go service—deployed as a macOS Launch Agent—handles queueing, policy enforcement, and result aggregation:

1. **Queue Management:** Redis Streams (or SQLite for single-node) maintain task queues per team.
2. **Policy Engine:** Encodes rules such as triggering Alert-Enricher within 30 seconds of a new red scenario and auto-retraining Red-Gen when more than two gaps are reported.
3. **Result Aggregation:** Normalises LLM responses back into SIEM indices for visibility.

Example REST contract:

```http
POST /tasks
{
  "team": "red|blue|purple",
  "type": "generate_scenario|enrich_alert|analyze_gap",
  "payload": { ... }
}
```

Responses are persisted in `task-results-*`, enabling Kibana dashboards that visualise the pipeline.

## 4. End-to-End Data Flow

1. **Red Scenario Generation:** The hub queues a `generate_scenario` task; Red-Gen returns a multi-stage attack captured in `red-scenarios-*`.
2. **Simulation / Injection:** A simulator replays benign equivalents within macOS sandboxes or emits expected telemetry which is forwarded to the SIEM.
3. **Blue-Team Enrichment:** Logs trigger the `enrich_alert` pipeline; Alert-Enricher adds `ml.red_match:true` plus ATT&CK annotations to `alerts-*`.
4. **Automatic Containment:** SOAR monitors for `ml.red_match:true`, invokes Playbook-Executor, and executes the containment sequence (MDM isolation, process termination, memory capture).
5. **Purple-Team Gap Analysis:** Post-incident, Gap-Analyzer creates a gap report and Metric-Synthesiser updates KPIs (detection rate, MTTD, MTTC).
6. **Continuous Improvement:** Model-Updater writes refined prompts to Git, CI rebuilds Docker images, and subsequent scenarios inherit improvements.

## 5. macOS-Centric Deployment Checklist

| Step | Action | Command / Tool |
|------|--------|----------------|
| 1 | Install container runtime | `brew install colima docker` |
| 2 | Pull quantised models | `./scripts/download.sh Llama-3-8B-Q4_K_M` |
| 3 | Build LLM containers | Dockerfile embedding `llama.cpp` server and quantised model. |
| 4 | Set up Redis | `docker run -d --name redis -p 6379:6379 redis:7-alpine` |
| 5 | Deploy Orchestration Hub | `git clone ... && uvicorn main:app --host 0.0.0.0 --port 8000` |
| 6 | Connect SIEM | Forward `red-scenarios-*`, `alerts-*`, `purple-gaps-*` to Elasticsearch. |
| 7 | Integrate SOAR | Configure webhook to `http://localhost:8000/playbook`. |
| 8 | Visualise | Build Kibana dashboards (scenario catalogue, enriched alerts, purple KPIs). |
| 9 | Test | Run `./scripts/demo.sh` to execute a full cycle. |
| 10 | Harden | Use read-only containers, encrypted APFS, rotate SIEM/SOAR keys every 90 days. |

## 6. Scaling and Future Enhancements

| Need | Extension |
|------|-----------|
| Higher throughput | Scale Red-Gen containers behind a load balancer; optionally adopt Llama-3-70B on dedicated GPU hardware exposed via gRPC. |
| Cross-platform coverage | Add Windows and Linux-focused Red-LLMs while sharing Blue-LLM resources. |
| Human-in-the-loop | Provide a web UI for approving or editing generated phishing content. |
| Zero-trust integration | Use OTEL traces with signed JWTs so only authorised LLM instances ingest data. |
| Model provenance | Store prompt, temperature, and model hash alongside each artifact in the SIEM. |
| Adaptive adversary | Allow Purple-LLM to feed next-generation prompts to Red-Gen, forming a co-evolutionary loop. |

## 7. Quick-Start Example

```bash
# 1️⃣ Run the built-in orchestration demo (spins up FastAPI + sample tasks)
./scripts/demo.sh

# 2️⃣ (Optional) Interact with the API manually
curl -s http://127.0.0.1:8000/tasks | jq
curl -s "http://127.0.0.1:8000/queue/next?team=red" | jq

# 3️⃣ (Optional) Integrate with external LLM containers following Section 5.
```

## 8. AI SOC Microservice

To complement the orchestration hub, the repository now includes an AI-powered SOC service located under `ai_soc/`. The service is a FastAPI application that ingests threat-intel feeds, behavioural telemetry, and human approvals, then generates actionable remediation plans and quota updates via an LLM-backed policy engine.

### Capabilities

- **Threat-Intel ingestion** – POST structured CTI events to `/threat-intel` to automatically raise alerts when new high/critical indicators are detected.
- **Behavioural analytics** – Stream telemetry (or post JSON documents) to `/telemetry`; spikes in outbound activity trigger alerts enriched with contextual metadata.
- **Automated response** – Every alert is paired with a remediation plan (policy patch + playbook steps) and an optional quota update that disables self-suggestion for malicious agents.
- **Kafka integration** – When `KAFKA_BOOTSTRAP_SERVERS` is provided, the service consumes `rbp.metrics`, `rbp.proposals`, and `rbp.approvals`, then publishes alerts to `rbp.alerts` and quota updates to `rbp.quota_updates`.

### Running the Service

```bash
# Start the AI SOC API on port 9000 (defaults can be overridden via env vars)
./scripts/run_ai_soc.sh

# Check health
curl -s http://127.0.0.1:9000/healthz

# Inject a telemetry spike
curl -s -X POST http://127.0.0.1:9000/telemetry \
  -H 'content-type: application/json' \
  -d '{
        "device_id": "mac-1234",
        "timestamp": "2024-06-10T12:00:00Z",
        "signals": {"outbound_connections": 400},
        "agent_id": "red-gen"
      }'

# Review generated alerts, remediations, and quota decisions
curl -s http://127.0.0.1:9000/alerts | jq
curl -s http://127.0.0.1:9000/remediations | jq
curl -s http://127.0.0.1:9000/quota-updates | jq
```

When Kafka is unavailable the service degrades gracefully to API-only mode; persistent state is stored under `data/ai-soc-state.json` so the Review Board can replay alerts and LLM guidance.

## 9. Repository Layout

```
.
├── ai_soc/
│   ├── main.py          # FastAPI AI SOC service
│   ├── service.py       # Detection + remediation coordinator
│   ├── kafka.py         # Optional Kafka bridge for telemetry/alerts
│   ├── models.py        # Pydantic schemas for alerts, remediations, quota updates
│   ├── config.py        # Environment-driven settings
│   ├── storage.py       # JSON persistence for generated artefacts
│   └── llm.py           # Stubbed Lumo inference wrapper
├── hub/
│   ├── main.py          # FastAPI entry point exposing the orchestration API
│   ├── orchestrator.py  # Async queues and task lifecycle logic
│   ├── models.py        # Pydantic models shared by the service
│   └── storage.py       # JSON-backed persistence layer for demo data
├── scripts/
│   ├── demo.sh          # Spins up the service and walks through Red→Blue→Purple tasks
│   ├── download.sh      # Convenience helper for fetching quantised GGUF models
│   └── run_ai_soc.sh    # Boots the AI SOC microservice
├── data/                # JSON store used by the demo service (auto-created)
├── requirements.txt     # Python dependencies for the orchestration hub
└── README.md
```

The included demo service mirrors the orchestration hub described earlier so
that the architecture can be exercised locally without external dependencies.

## 10. Key Takeaways

- Modular LLM instances give each team a focused skill set with modest compute requirements.
- Hierarchical orchestration (Red → Blue → Purple) enables continuous hardening through feedback loops.
- The entire stack operates on macOS workstations using quantised models and container tooling, yet scales to larger infrastructures.
- Persisting every artifact in the SIEM delivers auditability, KPI tracking, and reusable training material.
- The architecture transforms an AI-augmented SOC into a dynamic cyber range where attackers, defenders, and evaluators co-evolve.

