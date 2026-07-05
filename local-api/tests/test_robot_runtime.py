from fastapi.testclient import TestClient

from app.main import app


def test_expired_license_blocks_run_start():
    client = TestClient(app)
    client_id = client.post("/clients", json={"name": "Expired Co"}).json()["client_id"]
    event_id = client.post(
        "/events",
        json={"client_id": client_id, "name": "Expired Event", "robot_id": "X2U-009"},
    ).json()["event_id"]
    client.post(
        "/licenses",
        json={
            "event_id": event_id,
            "robot_id": "X2U-009",
            "license_type": "daily",
            "start_date": "2026-01-01",
            "end_date": "2026-01-02",
        },
    )
    script_id = client.post(
        f"/events/{event_id}/scripts",
        json={"name": "Welcome", "language": "en", "content": "Welcome."},
    ).json()["script_id"]
    scenario_id = client.post(
        f"/events/{event_id}/scenarios/publish",
        json={
            "template_id": "welcome_reception",
            "name": "Expired Welcome",
            "config": {"welcome_script_id": script_id},
        },
    ).json()["scenario_id"]
    run_id = client.post(
        "/runs",
        json={"event_id": event_id, "scenario_id": scenario_id, "robot_id": "X2U-009"},
    ).json()["run_id"]

    start = client.post(f"/runs/{run_id}/start")

    assert start.status_code == 403
    assert start.json()["detail"] == "license_inactive"


def test_safety_robot_rag_movement_and_visual_marker_simulations():
    client = TestClient(app)

    robot_command = client.post(
        "/robots/X2U-001/commands",
        json={"action_type": "tts", "payload": {"text": "Hello"}, "priority": 6},
    )
    assert robot_command.status_code == 200
    assert robot_command.json()["status"] == "completed"

    emergency = client.post("/safety/emergency-stop", json={"robot_id": "X2U-001"})
    assert emergency.status_code == 200
    assert emergency.json()["safety_state"] == "emergency_stopped"

    blocked_movement = client.post(
        "/robots/X2U-001/commands",
        json={"action_type": "locomotion", "payload": {"forward": 0.1}, "priority": 9},
    )
    assert blocked_movement.status_code == 409
    assert blocked_movement.json()["detail"] == "emergency_stop_active"

    reset = client.post("/safety/reset", json={"robot_id": "X2U-001"})
    assert reset.status_code == 200
    assert reset.json()["safety_state"] == "ready"

    rag = client.post(
        "/rag/product-intros",
        json={
            "product_name": "X2 Ultra",
            "language": "en",
            "duration_seconds": 30,
            "materials": "Humanoid service robot for reception, product demos, and event hosting.",
        },
    )
    assert rag.status_code == 200
    assert "X2 Ultra" in rag.json()["draft"]

    movement = client.post(
        "/movement/scripts/simulate",
        json={"robot_id": "X2U-001", "script": [{"type": "forward", "distance_m": 1.2}]},
    )
    assert movement.status_code == 200
    assert movement.json()["status"] == "completed"

    docking = client.post(
        "/visual-marker/docking/simulate",
        json={"robot_id": "X2U-001", "marker_id": 3, "stop_distance_m": 0.5},
    )
    assert docking.status_code == 200
    assert docking.json()["status"] == "docking_completed"
