import pathlib
import sys

from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "ai_soc"))

from ai_soc import create_app


def test_ingest_and_remediate_alert():
    app = create_app()
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}

        payload = {
            "source": "agent-1",
            "event_type": "network",
            "payload": {
                "indicator": "1.2.3.4",
                "severity": "high",
                "agent_id": "agent-1",
            },
        }
        response = client.post("/telemetry", json=payload)
        assert response.status_code == 200

        alerts = client.get("/alerts")
        assert alerts.status_code == 200
        alert_body = alerts.json()
        assert alert_body["alerts"], "alert list should not be empty"
        alert_id = alert_body["alerts"][0]["id"]

        remediate = client.post(f"/alerts/{alert_id}/remediate")
        assert remediate.status_code == 200
        data = remediate.json()
        assert data["alert_id"] == alert_id
        action_types = {action["action_type"] for action in data["actions"]}
        assert "opa_policy" in action_types
        assert "network_policy" in action_types
        assert "quota_update" in action_types
