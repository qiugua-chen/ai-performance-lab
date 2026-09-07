from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from ai_performance_lab.jtl import parse_jtl
from ai_performance_lab.metrics import calculate_metrics
from ai_performance_lab.rules import (
    EvaluationOutputExistsError,
    EvaluationStatus,
    evaluate_metrics,
    write_evaluation_json,
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

FAIL_SPEC_PATH = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "test_specs"
    / "rule-fail.yaml"
)

INVALID_SPEC_PATH = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "test_specs"
    / "rule-invalid.yaml"
)


def load_fixed_metrics():
    document = parse_jtl(FIXED_JTL_PATH)
    return calculate_metrics(document.samples)


def test_equal_boundaries_pass() -> None:
    metrics = load_fixed_metrics()
    spec = load_test_spec(PASS_SPEC_PATH)

    result = evaluate_metrics(
        metrics,
        spec,
    )

    assert result.status is EvaluationStatus.PASS
    assert result.failed_checks == ()


def test_valid_metrics_that_miss_thresholds_fail() -> None:
    metrics = load_fixed_metrics()
    spec = load_test_spec(FAIL_SPEC_PATH)

    result = evaluate_metrics(
        metrics,
        spec,
    )

    failed_names = {
        check.name
        for check in result.failed_checks
    }

    assert result.status is EvaluationStatus.FAIL
    assert failed_names == {
        "minimum_rps",
        "maximum_p95_ms",
        "minimum_success_rate",
    }


def test_insufficient_samples_are_invalid() -> None:
    metrics = load_fixed_metrics()
    spec = load_test_spec(INVALID_SPEC_PATH)

    result = evaluate_metrics(
        metrics,
        spec,
    )

    failed_names = {
        check.name
        for check in result.failed_checks
    }

    assert result.status is EvaluationStatus.INVALID
    assert "minimum_sample_count" in failed_names

    assert all(
        check.category == "validity"
        for check in result.checks
    )


def test_inconsistent_counts_are_invalid() -> None:
    metrics = replace(
        load_fixed_metrics(),
        success_count=9,
        error_count=2,
    )
    spec = load_test_spec(PASS_SPEC_PATH)

    result = evaluate_metrics(
        metrics,
        spec,
    )

    failed_names = {
        check.name
        for check in result.failed_checks
    }

    assert result.status is EvaluationStatus.INVALID
    assert "sample_count_consistency" in failed_names
    assert "success_rate_consistency" in failed_names


def test_evaluation_json_is_not_overwritten(
    tmp_path: Path,
) -> None:
    metrics = load_fixed_metrics()
    spec = load_test_spec(PASS_SPEC_PATH)
    result = evaluate_metrics(
        metrics,
        spec,
    )
    output_path = tmp_path / "evaluation.json"

    write_evaluation_json(
        result,
        output_path,
    )

    first_content = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    with pytest.raises(
        EvaluationOutputExistsError
    ):
        write_evaluation_json(
            result,
            output_path,
        )

    second_content = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert second_content == first_content
    assert first_content["status"] == "PASS"