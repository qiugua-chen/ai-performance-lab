from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_performance_lab.jtl import (
    JTLDocument,
    JTLSample,
    parse_jtl,
)
from ai_performance_lab.metrics import (
    MetricsEmptyError,
    MetricsInvalidWindowError,
    MetricsOutputExistsError,
    calculate_metrics,
    write_metrics_json,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXED_JTL_PATH = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "jtl"
    / "fixed-metrics.jtl"
)


def test_fixed_dataset_matches_manual_calculation() -> None:
    document = parse_jtl(FIXED_JTL_PATH)

    metrics = calculate_metrics(document.samples)

    assert metrics.request_count == 10
    assert metrics.success_count == 8
    assert metrics.error_count == 2

    assert metrics.duration_seconds == 10.0
    assert metrics.rps == 1.0

    assert metrics.success_rate == 0.8
    assert metrics.error_rate == 0.2

    assert metrics.min_ms == 100
    assert metrics.avg_ms == 550.0
    assert metrics.max_ms == 1000

    assert metrics.p50_ms == 500
    assert metrics.p90_ms == 900
    assert metrics.p95_ms == 1000
    assert metrics.p99_ms == 1000


def test_metrics_do_not_depend_on_sample_order() -> None:
    document = parse_jtl(FIXED_JTL_PATH)

    original_metrics = calculate_metrics(
        document.samples
    )
    reversed_metrics = calculate_metrics(
        tuple(reversed(document.samples))
    )

    assert reversed_metrics == original_metrics


def test_empty_samples_are_rejected() -> None:
    with pytest.raises(MetricsEmptyError):
        calculate_metrics(())


def test_zero_duration_window_is_rejected() -> None:
    sample = JTLSample(
        timestamp_ms=1000000,
        elapsed_ms=0,
        label="HTTP GET",
        response_code="200",
        success=True,
    )

    with pytest.raises(MetricsInvalidWindowError):
        calculate_metrics((sample,))


def test_metrics_json_is_not_overwritten(
    tmp_path: Path,
) -> None:
    document = parse_jtl(FIXED_JTL_PATH)
    metrics = calculate_metrics(document.samples)
    output_path = tmp_path / "metrics.json"

    write_metrics_json(
        metrics,
        output_path,
    )

    first_content = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    with pytest.raises(MetricsOutputExistsError):
        write_metrics_json(
            metrics,
            output_path,
        )

    second_content = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert second_content == first_content
    assert first_content["request_count"] == 10
    assert first_content["p95_ms"] == 1000