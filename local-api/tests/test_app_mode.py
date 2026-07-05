from fastapi.testclient import TestClient

from app.main import app


def test_get_app_mode_defaults_to_admin():
    client = TestClient(app)

    response = client.get("/app-mode")

    assert response.status_code == 200
    assert response.json() == {
        "mode": "admin",
        "available_modes": ["admin", "operator"],
    }
