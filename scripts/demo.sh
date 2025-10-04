#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"
BASE_URL="http://$HOST:$PORT"

python -m venv .venv >/dev/null 2>&1 || true
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

uvicorn hub.main:app --host "$HOST" --port "$PORT" --log-level warning &
SERVER_PID=$!
trap 'kill "$SERVER_PID" >/dev/null 2>&1 || true' EXIT

for _ in {1..20}; do
  if curl -fs "$BASE_URL/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

python <<'PY'
import json
import urllib.parse
import urllib.request

BASE_URL = "http://127.0.0.1:8000"

def post(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        urllib.parse.urljoin(BASE_URL, path),
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as response:
        return json.load(response)


def get(path, query=None):
    if query:
        path = f"{path}?{urllib.parse.urlencode(query)}"
    with urllib.request.urlopen(urllib.parse.urljoin(BASE_URL, path)) as response:
        return json.load(response)

print("Creating sample tasks...")
red_task = post("/tasks", {
    "team": "red",
    "type": "generate_scenario",
    "payload": {"goal": "steal Documents folder"}
})
print("Red task:", json.dumps(red_task, indent=2))

envelope = get("/queue/next", {"team": "red"})
print("Dequeued for red team:", json.dumps(envelope, indent=2))

result = post(f"/tasks/{red_task['id']}/result", {
    "result": {"status": "scenario_generated", "scenario_id": "red-scenarios-demo"}
})
print("Result acknowledged:", json.dumps(result, indent=2))

blue_task = post("/tasks", {
    "team": "blue",
    "type": "enrich_alert",
    "payload": {"scenario_id": "red-scenarios-demo", "log_id": "alert-1"}
})
print("Blue task created:", json.dumps(blue_task, indent=2))

envelope_blue = get("/queue/next", {"team": "blue"})
print("Dequeued for blue team:", json.dumps(envelope_blue, indent=2))

post(f"/tasks/{blue_task['id']}/result", {
    "result": {"ml.red_match": True, "technique": "T1059"}
})

purple_task = post("/tasks", {
    "team": "purple",
    "type": "analyze_gap",
    "payload": {"scenario_id": "red-scenarios-demo", "detections": ["T1059"]}
})
print("Purple task created:", json.dumps(purple_task, indent=2))

envelope_purple = get("/queue/next", {"team": "purple"})
print("Dequeued for purple team:", json.dumps(envelope_purple, indent=2))

post(f"/tasks/{purple_task['id']}/result", {
    "result": {"gaps": [], "summary": "All techniques detected"}
})

print("\nAll tasks:")
print(json.dumps(get("/tasks"), indent=2))
PY

echo "Demo complete."
