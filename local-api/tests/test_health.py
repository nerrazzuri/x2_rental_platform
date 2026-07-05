from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_desktop_local_api_identity():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "x2-local-api",
        "mode": "windows-desktop",
    }
