import pytest

from app.services.traditional_engine import analyze_traditional


@pytest.mark.parametrize(
    ("message", "expected_category"),
    [
        ("No puedo iniciar sesión con mi cuenta", "ACCESS"),
        ("La aplicación muestra un error al guardar", "BUG"),
        ("Quiero agregar una nueva funcionalidad", "FEATURE"),
        ("Detecté una vulnerabilidad en el endpoint", "SECURITY"),
    ],
)
def test_category(message: str, expected_category: str) -> None:
    result = analyze_traditional(message)
    assert result.category == expected_category
    assert result.mode == "traditional"
    assert result.response


def test_security_requires_human_review() -> None:
    result = analyze_traditional("Hay una brecha por acceso no autorizado")
    assert result.category == "SECURITY"
    assert result.requiresHumanReview is True
    assert result.priority == "CRITICAL"


def test_security_keyword_has_priority_over_other_categories() -> None:
    result = analyze_traditional("Tengo un error y creo que hay una vulnerabilidad")
    assert result.category == "SECURITY"
