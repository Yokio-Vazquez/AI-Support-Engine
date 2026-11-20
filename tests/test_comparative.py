import json
from pathlib import Path

import pytest

from app.comparative import ComparativeCase, _record, load_cases
from app.schemas import AnalysisResult


def test_comparative_dataset_has_required_case_coverage() -> None:
    cases = load_cases()

    assert len(cases) >= 10
    assert sum(case.scenario == "ambiguous" for case in cases) >= 1
    assert sum(case.scenario == "prompt_injection" for case in cases) >= 2


def test_comparative_dataset_rejects_duplicate_ids(tmp_path: Path) -> None:
    case = {
        "case_id": "duplicate",
        "scenario": "normal",
        "message": "No puedo iniciar sesión.",
        "expected_category": "ACCESS",
        "expected_priority": "MEDIUM",
        "expected_requires_human_review": False,
    }
    cases_path = tmp_path / "cases.json"
    cases_path.write_text(
        json.dumps([case] * 10),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="IDs must be unique"):
        load_cases(cases_path)


def test_comparison_marks_category_and_priority_separately() -> None:
    case = ComparativeCase(
        case_id="access",
        scenario="normal",
        message="No puedo iniciar sesión.",
        expected_category="ACCESS",
        expected_priority="HIGH",
        expected_requires_human_review=False,
    )
    result = AnalysisResult(
        category="ACCESS",
        priority="MEDIUM",
        response="Verifique sus credenciales.",
        requiresHumanReview=False,
        mode="traditional",
    )

    row = _record(case, "traditional", result)

    assert row["format_valid"] is True
    assert row["category_correct"] is True
    assert row["priority_correct"] is False
    assert row["classification_correct"] is False


def test_comparison_records_provider_errors_as_invalid_rows() -> None:
    case = ComparativeCase(
        case_id="security",
        scenario="normal",
        message="Detecté una vulnerabilidad.",
        expected_category="SECURITY",
        expected_priority="HIGH",
        expected_requires_human_review=True,
    )

    row = _record(case, "generative", None, "Provider is unavailable.")

    assert row["format_valid"] is False
    assert row["classification_correct"] is False
    assert row["error"] == "Provider is unavailable."
