from fastapi.testclient import TestClient
from types import SimpleNamespace

from app import robot_adapters as adapters
from app.main import app


def test_default_robot_adapter_status_reports_mock_mode():
    client = TestClient(app)

    response = client.get("/robot-adapter/status")

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "mock"
    assert body["available"] is True
    assert body["transport"] == "simulated"
    assert body["supported_actions"]["tts"]["aimdk_service"] == "/aimdk_5Fmsgs/srv/PlayTts"
    assert body["supported_actions"]["screen_video"]["aimdk_service"] == "/face_ui_proxy/play_video"
    assert body["supported_actions"]["emoji"]["aimdk_service"] == "/face_ui_proxy/play_emoji"
    assert body["supported_actions"]["locomotion"]["aimdk_topic"] == "/aima/mc/locomotion/velocity"


def test_mock_robot_command_receipt_includes_adapter_contract():
    client = TestClient(app)

    response = client.post(
        "/robots/X2U-ADAPTER-001/commands",
        json={"action_type": "tts", "payload": {"text": "Hello from mock"}, "priority": 6},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["adapter"] == "mock"
    assert body["transport"] == "simulated"
    assert body["target"]["aimdk_service"] == "/aimdk_5Fmsgs/srv/PlayTts"


def test_aimdk_mode_fails_closed_when_ros_runtime_is_missing(monkeypatch):
    monkeypatch.setenv("X2_ROBOT_ADAPTER", "aimdk")
    client = TestClient(app)

    response = client.post(
        "/robots/X2U-ADAPTER-002/commands",
        json={"action_type": "tts", "payload": {"text": "Hello from AimDK"}, "priority": 6},
    )

    assert response.status_code == 503
    body = response.json()
    assert body["detail"]["error"] == "aimdk_runtime_unavailable"
    assert "rclpy" in body["detail"]["missing_dependencies"]


def test_sdk_audio_path_split_keeps_trailing_directory_separator():
    file_path, file_name = adapters.resolve_audio_file_parts(
        {"absolute_path": "/agibot/data/var/interaction/tts_cache/normal/demo.wav"}
    )

    assert file_path == "/agibot/data/var/interaction/tts_cache/normal/"
    assert file_name == "demo.wav"


def test_sdk_running_common_task_response_counts_as_accepted():
    response = SimpleNamespace(
        response=SimpleNamespace(
            header=SimpleNamespace(code=2),
            state=SimpleNamespace(value=400),
            task_id=123,
        )
    )

    assert adapters.response_succeeded(response) is True


def test_empty_ros_response_does_not_count_as_success():
    assert adapters.response_succeeded(None) is False


def test_sdk_request_timestamp_paths_are_stamped():
    assert hasattr(adapters, "stamp_ros_request")
    stamp = SimpleNamespace(sec=100, nanosec=200)
    node = SimpleNamespace(clock=SimpleNamespace(now=lambda: SimpleNamespace(to_msg=lambda: stamp)))
    node.get_clock = lambda: node.clock
    requests = [
        SimpleNamespace(header=SimpleNamespace(header=SimpleNamespace(stamp=None))),
        SimpleNamespace(request=SimpleNamespace(header=SimpleNamespace(stamp=None))),
        SimpleNamespace(header=SimpleNamespace(stamp=None)),
    ]

    for request in requests:
        assert adapters.stamp_ros_request(request, node) is True

    assert requests[0].header.header.stamp is stamp
    assert requests[1].request.header.stamp is stamp
    assert requests[2].header.stamp is stamp
