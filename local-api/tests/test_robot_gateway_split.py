import json
import urllib.error
from io import BytesIO

from fastapi.testclient import TestClient

from app import robot_gateway_client
from app.main import create_app


def test_business_role_exposes_business_routes_and_uses_local_mock_by_default(monkeypatch):
    monkeypatch.delenv("X2_ROBOT_GATEWAY_URL", raising=False)
    client = TestClient(create_app(role="business"))

    clients = client.get("/clients")
    adapter_status = client.get("/robot-adapter/status")

    assert clients.status_code == 200
    assert adapter_status.status_code == 200
    assert adapter_status.json()["execution_location"] == "local"
    assert adapter_status.json()["mode"] == "mock"


def test_robot_gateway_role_exposes_only_robot_routes(monkeypatch):
    monkeypatch.delenv("X2_ROBOT_GATEWAY_URL", raising=False)
    client = TestClient(create_app(role="robot-gateway"))

    health = client.get("/health")
    clients = client.get("/clients")
    adapter_status = client.get("/robot-adapter/status")

    assert health.status_code == 200
    assert health.json()["role"] == "robot-gateway"
    assert clients.status_code == 404
    assert adapter_status.status_code == 200
    assert adapter_status.json()["execution_location"] == "pc2"


def test_business_robot_commands_forward_to_configured_pc2_gateway(monkeypatch):
    calls = []

    def fake_request_json(method, url, payload=None, timeout=5.0):
        calls.append({"method": method, "url": url, "payload": payload, "timeout": timeout})
        if method == "GET":
            return {"mode": "aimdk", "available": True, "transport": "ros2"}
        return {
            "robot_id": "X2U-PC2-001",
            "action_type": "tts",
            "payload": {"text": "hello pc2"},
            "priority": 6,
            "status": "completed",
            "adapter": "aimdk",
            "transport": "ros2",
            "target": {"aimdk_service": "/aimdk_5Fmsgs/srv/PlayTts"},
        }

    monkeypatch.setenv("X2_ROBOT_GATEWAY_URL", "http://10.0.1.41:8766/")
    monkeypatch.setattr(robot_gateway_client, "request_json", fake_request_json)
    client = TestClient(create_app(role="business"))

    status = client.get("/robot-adapter/status")
    command = client.post(
        "/robots/X2U-PC2-001/commands",
        json={"action_type": "tts", "payload": {"text": "hello pc2"}, "priority": 6},
    )

    assert status.status_code == 200
    assert status.json()["execution_location"] == "remote"
    assert status.json()["gateway_url"] == "http://10.0.1.41:8766"
    assert command.status_code == 200
    body = command.json()
    assert body["command_id"].startswith("command_")
    assert body["gateway_url"] == "http://10.0.1.41:8766"
    assert body["adapter"] == "aimdk"
    assert calls == [
        {"method": "GET", "url": "http://10.0.1.41:8766/robot-adapter/status", "payload": None, "timeout": 5.0},
        {
            "method": "POST",
            "url": "http://10.0.1.41:8766/robots/X2U-PC2-001/commands",
            "payload": {"action_type": "tts", "payload": {"text": "hello pc2"}, "priority": 6},
            "timeout": 5.0,
        },
    ]


def test_business_robot_gateway_422_response_stays_validation_error(monkeypatch):
    def fake_request_json(method, url, payload=None, timeout=5.0):
        raise robot_gateway_client.RobotGatewayHttpError(
            status_code=422,
            detail={"detail": {"error": "tts_text_required"}},
        )

    monkeypatch.setenv("X2_ROBOT_GATEWAY_URL", "http://10.0.1.41:8766")
    monkeypatch.setattr(robot_gateway_client, "request_json", fake_request_json)
    client = TestClient(create_app(role="business"))

    response = client.post(
        "/robots/X2U-PC2-001/commands",
        json={"action_type": "tts", "payload": {}, "priority": 6},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "tts_text_required"


def test_request_json_parses_error_body(monkeypatch):
    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(
            url=request.full_url,
            code=503,
            msg="Service Unavailable",
            hdrs={},
            fp=BytesIO(json.dumps({"detail": {"error": "aimdk_runtime_unavailable"}}).encode()),
        )

    monkeypatch.setattr(robot_gateway_client.urllib.request, "urlopen", fake_urlopen)

    try:
        robot_gateway_client.request_json("GET", "http://pc2/robot-adapter/status")
    except robot_gateway_client.RobotGatewayHttpError as exc:
        assert exc.status_code == 503
        assert exc.detail == {"detail": {"error": "aimdk_runtime_unavailable"}}
    else:
        raise AssertionError("expected RobotGatewayHttpError")
