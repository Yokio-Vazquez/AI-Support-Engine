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


def test_generative_engine_errors_are_reported(monkeypatch) -> None:
    from app.routes import analyze as analyze_route
    from app.services.generative_engine import GenerativeEngineError

    async def fail_analysis(message: str):
        raise GenerativeEngineError(503, "Generative engine is not configured.")

    monkeypatch.setattr(analyze_route, "analyze_generative", fail_analysis)
    response = client.post(
        "/api/analyze",
        json={"message": "Necesito ayuda", "mode": "generative"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Generative engine is not configured."


def test_generative_endpoint_returns_shared_contract(monkeypatch) -> None:
    from app.routes import analyze as analyze_route
    from app.schemas import AnalysisResult

    async def successful_analysis(message: str) -> AnalysisResult:
        return AnalysisResult(
            category="BUG",
            priority="MEDIUM",
            response="Revisaremos el problema.",
            requiresHumanReview=False,
            mode="generative",
        )

    monkeypatch.setattr(analyze_route, "analyze_generative", successful_analysis)
    response = client.post(
        "/api/analyze",
        json={"message": "El sistema muestra un error", "mode": "generative"},
    )

    assert response.status_code == 200
    assert response.json()["category"] == "BUG"
    assert response.json()["mode"] == "generative"
