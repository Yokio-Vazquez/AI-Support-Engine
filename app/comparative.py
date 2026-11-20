import argparse
import asyncio
import csv
import json
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas import AnalysisResult, Category, Priority
from app.services.generative_engine import (
    GenerativeEngineError,
    analyze_generative,
)
from app.services.traditional_engine import analyze_traditional


ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / "data" / "comparative_cases.json"
DEFAULT_RESULTS_PATH = ROOT / "results" / "comparative_results.csv"
MODES = ("traditional", "generative")


class ComparativeCase(BaseModel):
    case_id: str
    scenario: Literal["normal", "ambiguous", "prompt_injection"]
    message: str = Field(min_length=1, max_length=4000)
    expected_category: Category
    expected_priority: Priority
    expected_requires_human_review: bool


def load_cases(path: Path = CASES_PATH) -> list[ComparativeCase]:
    try:
        raw_cases = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not load comparative cases from {path}.") from exc

    if not isinstance(raw_cases, list) or len(raw_cases) < 10:
        raise ValueError("The comparative dataset must contain at least 10 cases.")

    cases = [ComparativeCase.model_validate(case) for case in raw_cases]
    if len({case.case_id for case in cases}) != len(cases):
        raise ValueError("Comparative case IDs must be unique.")
    if sum(case.scenario == "prompt_injection" for case in cases) < 2:
        raise ValueError("The dataset must contain at least two prompt-injection cases.")
    return cases


def _record(
    case: ComparativeCase,
    mode: str,
    result: AnalysisResult | None,
    error: str = "",
) -> dict[str, Any]:
    if result is None:
        return {
            "case_id": case.case_id,
            "scenario": case.scenario,
            "mode": mode,
            "message": case.message,
            "expected_category": case.expected_category,
            "category": "",
            "expected_priority": case.expected_priority,
            "priority": "",
            "expected_requires_human_review": case.expected_requires_human_review,
            "requires_human_review": "",
            "format_valid": False,
            "category_correct": False,
            "priority_correct": False,
            "classification_correct": False,
            "human_review_correct": False,
            "error": error,
        }

    validated = AnalysisResult.model_validate(result.model_dump())
    format_valid = validated.mode == mode and bool(validated.response.strip())
    category_correct = validated.category == case.expected_category
    priority_correct = validated.priority == case.expected_priority
    human_review_correct = (
        validated.requiresHumanReview == case.expected_requires_human_review
    )
    return {
        "case_id": case.case_id,
        "scenario": case.scenario,
        "mode": mode,
        "message": case.message,
        "expected_category": case.expected_category,
        "category": validated.category,
        "expected_priority": case.expected_priority,
        "priority": validated.priority,
        "expected_requires_human_review": case.expected_requires_human_review,
        "requires_human_review": validated.requiresHumanReview,
        "format_valid": format_valid,
        "category_correct": category_correct,
        "priority_correct": priority_correct,
        "classification_correct": category_correct and priority_correct,
        "human_review_correct": human_review_correct,
        "error": error,
    }


async def run_comparison(cases: list[ComparativeCase]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for case in cases:
        traditional_result = analyze_traditional(case.message)
        records.append(_record(case, "traditional", traditional_result))

        try:
            generative_result = await analyze_generative(case.message)
        except GenerativeEngineError as exc:
            records.append(_record(case, "generative", None, exc.detail))
        else:
            records.append(_record(case, "generative", generative_result))
    return records


def write_results(records: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        raise ValueError("No comparative results to write.")

    with output_path.open("w", newline="", encoding="utf-8-sig") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def _percentage(records: list[dict[str, Any]], field: str) -> float:
    if not records:
        return 0.0
    return 100 * sum(bool(record[field]) for record in records) / len(records)


def print_summary(records: list[dict[str, Any]]) -> None:
    for mode in MODES:
        mode_records = [record for record in records if record["mode"] == mode]
        print(f"\n{mode} ({len(mode_records)} casos)")
        print(f"  Formato válido: {_percentage(mode_records, 'format_valid'):.1f}%")
        print(
            "  Categoría correcta: "
            f"{_percentage(mode_records, 'category_correct'):.1f}%"
        )
        print(
            "  Prioridad correcta: "
            f"{_percentage(mode_records, 'priority_correct'):.1f}%"
        )
        print(
            "  Clasificación exacta (categoría y prioridad): "
            f"{_percentage(mode_records, 'classification_correct'):.1f}%"
        )
        print(
            "  Revisión humana correcta: "
            f"{_percentage(mode_records, 'human_review_correct'):.1f}%"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the real-provider and traditional comparative evaluation."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_RESULTS_PATH,
        help="CSV results path (default: results/comparative_results.csv)",
    )
    args = parser.parse_args()

    if not os.getenv("OPENROUTER_API_KEY", "").strip() or not os.getenv(
        "OPENROUTER_MODEL", ""
    ).strip():
        parser.error(
            "Configure OPENROUTER_API_KEY and OPENROUTER_MODEL in .env before running."
        )

    try:
        cases = load_cases()
    except ValueError as exc:
        parser.error(str(exc))

    records = asyncio.run(run_comparison(cases))
    write_results(records, args.output)
    print_summary(records)
    print(f"\nResultados guardados en: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
