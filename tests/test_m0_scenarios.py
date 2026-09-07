from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ai_performance_lab.jtl import parse_jtl
from ai_performance_lab.metrics import calculate_metrics
from ai_performance_lab.rules import (
    EvaluationResult,
    EvaluationStatus,
    evaluate_metrics,
)
from ai_performance_lab.test_spec.loader import load_test_spec


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FIXED_JTL_PATH = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "jtl"
    / "fixed-metrics.jtl"
)

PASS_SPEC_PATH = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "test_specs"
    / "rule-pass.yaml"
)

JTL_HEADER = (
    "timeStamp,elapsed,label,responseCode,"
    "responseMessage,success"
)


def write_scenario_jtl(
    path: Path,
    elapsed_values: Sequence[int],
    success_values: Sequence[bool],
    interval_ms: int,
) -> None:
    if len(elapsed_values) != len(success_values):
        raise ValueError(
            "Elapsed and success datasets must have the same length."
        )

    lines = [JTL_HEADER]
    base_timestamp_ms = 1_000_000

    for index, (elapsed_ms, success) in enumerate(
        zip(
            elapsed_values,
            success_values,
            strict=True,
        )
    ):
        timestamp_ms = (
            base_timestamp_ms
            + index * interval_ms
        )
        response_code = "200" if success else "500"
        response_message = "OK" if success else "Error"
        success_text = "true" if success else "false"

        lines.append(
            f"{timestamp_ms},"
            f"{elapsed_ms},"
            f"HTTP GET,"
            f"{response_code},"
            f"{response_message},"
            f"{success_text}"
        )

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def evaluate_jtl(
    jtl_path: Path,
) -> EvaluationResult:
    document = parse_jtl(jtl_path)
    metrics = calculate_metrics(document.samples)
    spec = load_test_spec(PASS_SPEC_PATH)

    return evaluate_metrics(
        metrics,
        spec,
    )


def failed_check_names(
    result: EvaluationResult,
) -> set[str]:
    return {
        check.name
        for check in result.failed_checks
    }


def test_normal_scenario_passes() -> None:
    result = evaluate_jtl(FIXED_JTL_PATH)

    assert result.status is EvaluationStatus.PASS
    assert result.failed_checks == ()


def test_slow_scenario_fails_p95(
    tmp_path: Path,
) -> None:
    jtl_path = tmp_path / "slow.jtl"

    write_scenario_jtl(
        path=jtl_path,
        elapsed_values=[1500] * 10,
        success_values=[True] * 10,
        interval_ms=900,
    )

    result = evaluate_jtl(jtl_path)

    assert result.status is EvaluationStatus.FAIL
    assert failed_check_names(result) == {
        "maximum_p95_ms",
    }


def test_error_scenario_fails_success_rate(
    tmp_path: Path,
) -> None:
    jtl_path = tmp_path / "error.jtl"

    write_scenario_jtl(
        path=jtl_path,
        elapsed_values=[100] * 10,
        success_values=[
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            False,
            False,
            False,
        ],
        interval_ms=1000,
    )

    result = evaluate_jtl(jtl_path)

    assert result.status is EvaluationStatus.FAIL
    assert failed_check_names(result) == {
        "minimum_success_rate",
    }


def test_insufficient_samples_are_invalid(
    tmp_path: Path,
) -> None:
    jtl_path = tmp_path / "invalid.jtl"

    write_scenario_jtl(
        path=jtl_path,
        elapsed_values=[100] * 5,
        success_values=[True] * 5,
        interval_ms=500,
    )

    result = evaluate_jtl(jtl_path)

    assert result.status is EvaluationStatus.INVALID
    assert failed_check_names(result) == {
        "minimum_sample_count",
    }