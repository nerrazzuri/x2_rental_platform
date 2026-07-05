from fastapi.testclient import TestClient

from app.main import app


def test_product_presenter_workflow_runs_from_admin_setup_to_operator_console():
    client = TestClient(app)

    create_client = client.post("/clients", json={"name": "ABC Tech", "contact_name": "Liang"})
    assert create_client.status_code == 201
    client_id = create_client.json()["client_id"]

    create_event = client.post(
        "/events",
        json={
            "client_id": client_id,
            "name": "ABC Product Launch",
            "robot_id": "X2U-001",
            "language": "zh-CN",
        },
    )
    assert create_event.status_code == 201
    event_id = create_event.json()["event_id"]

    license_response = client.post(
        "/licenses",
        json={
            "event_id": event_id,
            "robot_id": "X2U-001",
            "license_type": "weekly",
            "start_date": "2026-07-01",
            "end_date": "2026-07-07",
        },
    )
    assert license_response.status_code == 201
    assert license_response.json()["status"] == "active"

    asset = client.post(
        f"/events/{event_id}/assets",
        json={
            "asset_type": "video",
            "name": "product_a.mp4",
            "uri": "local://assets/product_a.mp4",
            "mime_type": "video/mp4",
        },
    )
    assert asset.status_code == 201
    asset_id = asset.json()["asset_id"]

    script = client.post(
        f"/events/{event_id}/scripts",
        json={
            "name": "Product A Intro",
            "language": "zh-CN",
            "content": "大家好，接下来为您介绍我们的核心产品。",
        },
    )
    assert script.status_code == 201
    script_id = script.json()["script_id"]

    templates = client.get("/templates")
    assert templates.status_code == 200
    assert any(template["template_id"] == "product_presenter" for template in templates.json())

    publish = client.post(
        f"/events/{event_id}/scenarios/publish",
        json={
            "template_id": "product_presenter",
            "name": "Product Presenter Main Flow",
            "config": {
                "product_name": "Product A",
                "screen_asset_id": asset_id,
                "intro_script_id": script_id,
                "motion_id": "right_hand_raise",
            },
        },
    )
    assert publish.status_code == 201
    scenario_id = publish.json()["scenario_id"]

    run = client.post(
        "/runs",
        json={"event_id": event_id, "scenario_id": scenario_id, "robot_id": "X2U-001"},
    )
    assert run.status_code == 201
    run_id = run.json()["run_id"]

    start = client.post(f"/runs/{run_id}/start")
    assert start.status_code == 200
    assert start.json()["status"] == "running"
    assert start.json()["current_step_id"] == "opening"

    next_step = client.post(f"/runs/{run_id}/next")
    assert next_step.status_code == 200
    assert next_step.json()["current_step_id"] == "product_intro"

    logs = client.get(f"/events/{event_id}/logs")
    assert logs.status_code == 200
    log_types = {entry["type"] for entry in logs.json()}
    assert {"scenario_published", "robot_command"}.issubset(log_types)
