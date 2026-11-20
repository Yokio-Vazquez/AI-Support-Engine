from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_traditional_endpoint() -> None:
    response = client.post(
        "/api/analyze",
        json={"message": "No puedo iniciar sesión", "mode": "traditional"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "ACCESS"
    assert body["mode"] == "traditional"
    assert body["priority"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert isinstance(body["requiresHumanReview"], bool)


def test_empty_message_is_rejected() -> None:
    response = client.post(
        "/api/analyze",
        json={"message": "   ", "mode": "traditional"},
    )
    assert response.status_code == 422


def test_invalid_mode_is_rejected() -> None:
    response = client.post(
        "/api/analyze",
        json={"message": "Hola", "mode": "unknown"},
    )
    assert response.status_code == 422
