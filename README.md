# AI-Powered Security Operations Center (AI SOC)

This repository captures a modular, hierarchical architecture for an AI-augmented security operations center that you can run on macOS endpoints or a small fleet of Macs. The design fuses specialised Red-, Blue-, and Purple-team large language models with an orchestration hub so that simulated adversaries, automated defenders, and evaluators continuously sharpen one another while protecting real devices.

---

## Quick Start

Get the entire stack running in minutes with Docker:

```bash
# One-command deployment
./scripts/quick-start.sh

# Or use Make for more control
make deploy
```

For detailed deployment instructions, configuration options, and troubleshooting, see **[DEPLOYMENT.md](DEPLOYMENT.md)**.

---

## AI SOC Layers and How They Defend Your Devices

| AI SOC Layer | Core Function | How It Protects Your Devices |
| --- | --- | --- |
| **1️⃣ Threat-Intelligence Ingestion** | Continuously ingest CTI feeds, vulnerability databases, and OS-level advisories, normalising them into structured events. | Detects newly disclosed exploits that affect the macOS VM, self-hosted agents, or GrapheneOS devices, and auto-tags relevant CVEs in the audit ledger so the quota manager can halt risky self-suggestions. |
| **2️⃣ Behavioural Analytics & Anomaly Detection** | Streams raw logs (network flows, system calls, OPA decisions, agent metrics) into an LLM-assisted baseline that profiles each device and user. | Flags sudden surges in outbound connections or abnormal policy changes (e.g., a compromised Red agent widening its target range) before approvals occur. |
| **3️⃣ Automated Response & Orchestration** | Generates remediation playbooks, policy updates, and containment scripts that flow through existing CI/CD and SOAR pipelines. | Pushes new OPA rules, revokes quota-manager permissions, or dispatches signed OTA updates that rotate keys and harden OS configurations without user intervention. |

### Interaction with the RBP Stack

```
+-------------------+          +-------------------+          +-------------------+
|   Device / End-   |  Tele-   |   Kafka (Events)  |  AI-SOC  |   FastAPI Review  |
|   point (Phone)   |<-------->|   (Proposals,     |<-------->|   Board (Human)   |
|   (GrapheneOS)    |  metrix  |   Metrics, Logs)  |  Engine  |   + Quota Mgr.    |
+-------------------+          +-------------------+          +-------------------+
                                 ^   ^   ^
                                 |   |   |
                                 |   |   +--- OPA policy engine (enforcement)
                                 |   +------- Lumo API (self-suggest)
                                 +----------- Audit Ledger (immutable)
```

- Every device—GrapheneOS phones, macOS VMs, Kubernetes pods—streams telemetry to Kafka topics already used by the Red/Blue/Purple (RBP) pipeline.
- The AI SOC consumes the same feeds, augments them with LLM-driven anomaly detection, and publishes enriched alerts to `rbp.alerts`.
- The human-in-the-loop FastAPI Review Board inspects alerts, approves or rejects automated remediations, and coordinates with the quota manager.
- When critical alerts are confirmed, the quota manager flips `SELF_SUGGEST_ENABLED` for the offending agent, instantly preventing further self-deployed changes.

### Concrete Protection Scenarios

| Scenario | AI SOC Action | Result for Your Device |
| --- | --- | --- |
| New zero-day CVE for the macOS kernel is discovered. | CTI ingestion cross-references the VM inventory, auto-creates an OPA rule that blocks privileged operations matching the vulnerable syscall pattern. | The macOS VM (and any connected devices) is shielded until patches are applied. |
| Compromised Red agent attempts data exfiltration. | Behavioural analytics flag the outbound spike, generate a containment playbook, and publish a `NetworkPolicy` that isolates the pod while revoking its API token. | The malicious agent is quarantined before it reaches external services or personal devices. |
| Your Pixel receives a phishing-laden attachment. | Endpoint telemetry sends a hash to Kafka; the AI SOC matches it to known malicious signatures and issues a `DevicePolicy` update blocking that MIME type. | The payload is neutralised on-device with no user action required. |
| Repeated false-positive alerts from a noisy sensor. | The AI SOC recommends a tuned OPA rule that introduces a tolerance window and asks the Review Board to approve it. | Noise is reduced so genuine threats rise to the top, preventing alert fatigue. |

---

## Operational Runbook

1. **Deploy the AI SOC microservice** – A FastAPI wrapper around the Lumo inference API lives in `ai_soc/`. Install with Poetry and expose it on port `9000`.
   ```bash
   cd ai_soc/
   poetry install
   uvicorn ai_soc.main:app --host 0.0.0.0 --port 9000
   ```
2. **Subscribe to telemetry** – Add Kafka consumers for `rbp.metrics`, `rbp.proposals`, and `rbp.approvals`, feeding events to the AI SOC engine.
3. **Load threat-intel feeds** – Pull CVE and indicator streams (e.g., `https://feeds.cve.org/`, `https://otx.alienvault.com/api/v1/indicators`) and normalise them for scoring.
4. **Define remediation prompts** – Craft prompt templates that instruct Lumo to translate alerts into policy YAML, scripts, or Kubernetes patches.
5. **Expose alert APIs** – Publish `/alerts` endpoints consumed by the Review Board UI so analysts can triage AI-generated recommendations.
6. **Integrate the quota manager** – When the AI SOC marks an agent as malicious, emit `rbp.quota_updates` messages that flip `SELF_SUGGEST_ENABLED` to false.

> All bootstrap steps are encoded in the generated `manifest.yaml`; run the repository’s bootstrap script once to provision Kafka topics, ConfigMaps, and service accounts.

### Best Practices for Device-Centric Protection

| Practice | Why It Matters | How to Implement |
| --- | --- | --- |
| Zero-Trust Network Segmentation | Limits lateral movement from compromised pods or devices. | Use Kubernetes `NetworkPolicy` objects generated by the AI SOC and enable per-app VPN profiles on GrapheneOS. |
| Signed OTA Updates | Ensures only authentic binaries reach endpoints. | Store the signing key fingerprint in the `agent-flags` ConfigMap; allow the AI SOC to rotate keys and distribute fresh signatures post-incident. |
| Immutable Audit Ledger | Provides non-repudiation for SOC actions. | Post every AI SOC alert, remediation, and approval to the existing QLDB-style audit ledger shared with the RBP pipeline. |
| Human-in-the-Loop Review Board | Prevents false positives from disrupting production. | Present AI-generated remediations with risk scores; require analyst approval before enforcement. |
| Periodic Model Retraining | Keeps behavioural baselines current as fleets evolve. | Nightly jobs export the last 30 days of telemetry, fine-tune the Lumo model, and redeploy updated detection weights. |

---

## LLM Suite Reference Architecture

While the AI SOC focuses on device protection, it sits alongside a specialised LLM triumvirate that continuously pressure-tests and strengthens the environment.

### High-Level Topology

```
+----------------------+      +----------------------+      +----------------------+
|   Red Team LLMs      | ---> |   Orchestration Hub  | <--- |   Blue Team LLMs     |
| (Attack-gen, Phishing,|      | (task router, queue, |      | (Alert-enrich,       |
|  Malware-craft)      |      |  policy engine)      |      |  Incident-playbooks) |
+----------------------+      +----------------------+      +----------------------+
                                 ^          |
                                 |          v
                         +---------------------------+
                         |   Purple Team LLM (Meta)  |
                         |  (Gap analysis, metric    |
                         |   synthesis, model update)|
                         +---------------------------+
```

All suites read and write shared artefacts in the SIEM (Elastic or OpenSearch) and trigger SOAR playbooks through the orchestration hub. Containers can be swapped or scaled independently.

### Red-Team LLM Suite

| Instance | Core Prompt / Role | Typical Output | Integration Point |
| --- | --- | --- | --- |
| **Red-Gen** | Generate realistic multi-stage attacks against macOS endpoints using publicly known exploits and custom payloads. | Attack playbooks, malicious binaries, phishing lures, C2 configuration. | Writes `red-scenario` documents to `red-scenarios-*`. |
| **Phish-LLM** | Compose spear-phishing content targeting specific personas. | Email body, subject, encoded attachments. | Enhances red scenarios with social-engineering vectors. |
| **Malware-Craft** | Produce macOS-compatible payloads for exfiltration or persistence. | Source code, compile commands, hashes. | Stores artefacts linked to scenario IDs. |
| **Adversary-Emulation** | Translate MITRE ATT&CK techniques (e.g., T1059) into macOS command snippets. | Shell commands, expected telemetry. | Supplies detection seeds for Blue-team rule generation. |

*Deployment tip:* Run each instance in lightweight Docker or Podman containers on macOS using quantised models such as `Llama-3-8B-Chat-Q4_K_M`, keeping RAM near 6 GB per container.

### Blue-Team LLM Suite

| Instance | Core Prompt / Role | Typical Output | Integration Point |
| --- | --- | --- | --- |
| **Alert-Enricher** | Cross-reference raw OSQuery logs against red scenarios. | Enriched alert JSON (`ml.red_match=true`, ATT&CK mappings). | Updates SIEM alerts (`alerts-*`). |
| **Detection-Builder** | Convert red scenarios into Sigma rules. | Sigma/YAML with Elastic/Kibana mappings. | Auto-loads into SIEM rule engine. |
| **Playbook-Executor** | Generate step-by-step containment actions when red-matched alerts trigger. | SOAR playbook JSON for Cortex XSOAR, Splunk SOAR, StackStorm. | Delivered via webhook from the hub. |
| **Forensic-Analyst** | Summarise incident timelines per host. | Narrative timeline, evidence list, artefact recommendations. | Attached to incident tickets. |

*Deployment tip:* These workloads benefit from larger reasoning models (e.g., `Mistral-7B-Instruct-v0.2`) accelerated with `llama.cpp` and Metal on Apple Silicon.

### Purple-Team LLM Suite

| Instance | Core Prompt / Role | Typical Output | Integration Point |
| --- | --- | --- | --- |
| **Gap-Analyzer** | Compare red scenarios against triggered detections to expose blind spots. | Gap reports, severity scores, missing ATT&CK techniques. | Writes to `purple-gaps-*`. |
| **Metric-Synthesiser** | Roll up detection-rate, MTTD, and MTTC across exercises. | KPI dashboards for Kibana. | Supports executive reporting. |
| **Model-Updater** | Suggest prompt and rule tweaks based on detected gaps. | Updated prompts and rule metadata. | Triggers CI/CD redeployments. |
| **Adversary-Defender Dialogue** | Simulate iterative attacker-versus-defender exchanges. | Dialogue transcripts. | Provides analyst training material. |

*Deployment tip:* A summarisation-scale model such as `Phi-2-7B` is sufficient given the structured inputs.

### Orchestration Hub

The hub is a thin Python or Go service (often a launch agent on macOS) that:

1. **Manages queues** – Redis Streams or SQLite maintain tasks per LLM family.
2. **Enforces policy** – Encodes rules such as triggering `Alert-Enricher` within 30 seconds of a new scenario or retraining `Red-Gen` when multiple gaps surface.
3. **Aggregates results** – Collects enriched alerts, detection rules, and gap reports into SIEM indices for auditing.

```json
POST /tasks
{
  "team": "red|blue|purple",
  "type": "generate_scenario|enrich_alert|analyze_gap",
  "payload": { /* scenario ID, logs, etc. */ }
}
```

Responses land in the `task-results-*` index for full lifecycle observability.

### End-to-End Data Flow

1. **Red scenario generation** – The hub queues `generate_scenario`; `Red-Gen` outputs a multi-stage attack stored in `red-scenarios-*`.
2. **Simulation / injection** – A sandboxed macOS VM replays benign equivalents, shipping telemetry to the SIEM.
3. **Blue-team enrichment** – New logs trigger `enrich_alert`; `Alert-Enricher` adds `ml.red_match:true` and ATT&CK tags.
4. **Automatic containment** – SOAR monitors for `ml.red_match:true`, invokes `Playbook-Executor`, and executes containment via MDM, process kills, and memory capture.
5. **Purple-team gap analysis** – After closure, the hub queues `analyze_gap`; `Gap-Analyzer` and `Metric-Synthesiser` update gap reports and KPIs.
6. **Continuous improvement** – `Model-Updater` writes prompt and rule adjustments to Git, CI/CD rebuilds containers, and the next scenario benefits from refinements.

### Deployment Checklist (macOS Centric)

| Step | Action | Tool / Command |
| --- | --- | --- |
| 1 | Install container runtime | `brew install colima docker` |
| 2 | Pull quantised models | `./download.sh Llama-3-8B-Q4_K_M` via `llama.cpp` |
| 3 | Build LLM containers | Dockerfile copies models and starts `./server -m model.bin -c 2048` |
| 4 | Set up Redis | `docker run -d --name redis -p 6379:6379 redis:7-alpine` |
| 5 | Deploy orchestration hub | `git clone … && uvicorn main:app --host 0.0.0.0 --port 8000` |
| 6 | Connect SIEM | Forward `red-scenarios-*`, `alerts-*`, `purple-gaps-*` to Elasticsearch (`http://localhost:9200`) |
| 7 | Integrate SOAR | Point webhooks (Cortex XSOAR, Splunk SOAR, StackStorm) at `http://localhost:8000/playbook` |
| 8 | Visualise | Build Kibana dashboards for scenarios, alerts, and gaps |
| 9 | Test | Run `demo.sh` to trigger a full red→blue→purple cycle |
| 10 | Harden | Run containers read-only, use encrypted APFS for models, rotate SIEM/SOAR keys every 90 days |

### Quick-Start Example

```bash
# 1️⃣ Start Redis and the orchestration hub
docker run -d --name redis -p 6379:6379 redis:7-alpine
uvicorn hub.main:app --host 0.0.0.0 --port 8000 &

# 2️⃣ Launch a Red-Gen container (quantised Llama-3-8B)
docker run -d --name red-gen \
  -e MODEL=/models/llama3-8b-q4_k_m.bin \
  -p 8081:8080 \
  myorg/llm-server:latest

# 3️⃣ Request a red scenario
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"team":"red","type":"generate_scenario","payload":{"goal":"steal Documents folder"}}'

# 4️⃣ Red-Gen response is stored in `red-scenarios-*`.
# 5️⃣ Blue-LLM enriches corresponding alerts within ~15 seconds.
# 6️⃣ Purple-LLM produces the gap report post-incident.
# 7️⃣ Review the "SOC Purple Loop" dashboard in Kibana.
```

---

## Key Takeaways

1. Ingests threat intelligence and raw telemetry from every endpoint (phones, macOS VMs, Kubernetes workloads).
2. Analyses behaviour with LLM-enhanced models to spot anomalies and emerging exploits quickly.
3. Generates machine-readable mitigations (OPA rules, network policies, OTA patches) that flow through existing governance safeguards.
4. Orchestrates responses via the RBP pipeline, automatically locking down malicious agents while preserving human approval gates.
5. Logs every action to an immutable ledger, providing auditable proof that devices were defended at the moment of attack.

By combining the AI SOC with the Red/Blue/Purple LLM suites you create a living cyber range where attackers, defenders, and evaluators co-evolve—yielding adaptive protection that scales from a single GrapheneOS phone to a fleet of macOS workstations.

