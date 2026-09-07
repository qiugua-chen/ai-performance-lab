from __future__ import annotations

from math import isclose

from ai_performance_lab.metrics import PerformanceMetrics
from ai_performance_lab.rules.models import (
    EvaluationResult,
    EvaluationStatus,
    RuleCheck,
)
from ai_performance_lab.test_spec.models import TestSpec


RATE_TOLERANCE = 0.000001


def _validity_checks(
    metrics: PerformanceMetrics,
    spec: TestSpec,
) -> list[RuleCheck]:
    request_count_positive = metrics.request_count > 0

    count_consistent = (
        metrics.success_count + metrics.error_count
        == metrics.request_count
    )

    duration_positive = metrics.duration_seconds > 0

    success_rate_in_range = (
        0.0 <= metrics.success_rate <= 1.0
    )
    error_rate_in_range = (
        0.0 <= metrics.error_rate <= 1.0
    )

    if request_count_positive:
        expected_success_rate = (
            metrics.success_count / metrics.request_count
        )
        expected_error_rate = (
            metrics.error_count / metrics.request_count
        )

        success_rate_consistent = isclose(
            metrics.success_rate,
            expected_success_rate,
            abs_tol=RATE_TOLERANCE,
        )
        error_rate_consistent = isclose(
            metrics.error_rate,
            expected_error_rate,
            abs_tol=RATE_TOLERANCE,
        )
    else:
        success_rate_consistent = False
        error_rate_consistent = False

    enough_samples = (
        metrics.request_count
        >= spec.acceptance.min_samples
    )

    return [
        RuleCheck(
            name="positive_request_count",
            category="validity",
            actual=metrics.request_count,
            operator=">=",
            expected=1,
            passed=request_count_positive,
            message=(
                "At least one JTL sample is required."
            ),
        ),
        RuleCheck(
            name="sample_count_consistency",
            category="validity",
            actual=(
                metrics.success_count
                + metrics.error_count
            ),
            operator="==",
            expected=metrics.request_count,
            passed=count_consistent,
            message=(
                "Success and error counts must equal "
                "the total request count."
            ),
        ),
        RuleCheck(
            name="positive_duration",
            category="validity",
            actual=metrics.duration_seconds,
            operator=">",
            expected=0,
            passed=duration_positive,
            message=(
                "The observed execution duration must be positive."
            ),
        ),
        RuleCheck(
            name="success_rate_range",
            category="validity",
            actual=metrics.success_rate,
            operator="between",
            expected=1.0,
            passed=success_rate_in_range,
            message=(
                "Success rate must be between 0.0 and 1.0."
            ),
        ),
        RuleCheck(
            name="error_rate_range",
            category="validity",
            actual=metrics.error_rate,
            operator="between",
            expected=1.0,
            passed=error_rate_in_range,
            message=(
                "Error rate must be between 0.0 and 1.0."
            ),
        ),
        RuleCheck(
            name="success_rate_consistency",
            category="validity",
            actual=metrics.success_rate,
            operator="==",
            expected=(
                round(
                    metrics.success_count
                    / metrics.request_count,
                    6,
                )
                if request_count_positive
                else 0.0
            ),
            passed=success_rate_consistent,
            message=(
                "Success rate must match the sample counts."
            ),
        ),
        RuleCheck(
            name="error_rate_consistency",
            category="validity",
            actual=metrics.error_rate,
            operator="==",
            expected=(
                round(
                    metrics.error_count
                    / metrics.request_count,
                    6,
                )
                if request_count_positive
                else 0.0
            ),
            passed=error_rate_consistent,
            message=(
                "Error rate must match the sample counts."
            ),
        ),
        RuleCheck(
            name="minimum_sample_count",
            category="validity",
            actual=metrics.request_count,
            operator=">=",
            expected=spec.acceptance.min_samples,
            passed=enough_samples,
            message=(
                "The Run must contain enough samples "
                "to form a valid conclusion."
            ),
        ),
    ]


def _threshold_checks(
    metrics: PerformanceMetrics,
    spec: TestSpec,
) -> list[RuleCheck]:
    return [
        RuleCheck(
            name="minimum_rps",
            category="threshold",
            actual=metrics.rps,
            operator=">=",
            expected=spec.acceptance.min_rps,
            passed=(
                metrics.rps
                >= spec.acceptance.min_rps
            ),
            message=(
                "Observed RPS must meet the minimum RPS."
            ),
        ),
        RuleCheck(
            name="maximum_p95_ms",
            category="threshold",
            actual=metrics.p95_ms,
            operator="<=",
            expected=spec.acceptance.p95_ms,
            passed=(
                metrics.p95_ms
                <= spec.acceptance.p95_ms
            ),
            message=(
                "Observed P95 must not exceed the maximum P95."
            ),
        ),
        RuleCheck(
            name="minimum_success_rate",
            category="threshold",
            actual=metrics.success_rate,
            operator=">=",
            expected=spec.acceptance.success_rate,
            passed=(
                metrics.success_rate
                >= spec.acceptance.success_rate
            ),
            message=(
                "Observed success rate must meet "
                "the minimum success rate."
            ),
        ),
    ]


def evaluate_metrics(
    metrics: PerformanceMetrics,
    spec: TestSpec,
) -> EvaluationResult:
    """Evaluate validated metrics against one Test Spec."""

    validity_checks = _validity_checks(
        metrics,
        spec,
    )

    if not all(
        check.passed
        for check in validity_checks
    ):
        return EvaluationResult(
            status=EvaluationStatus.INVALID,
            checks=tuple(validity_checks),
        )

    threshold_checks = _threshold_checks(
        metrics,
        spec,
    )

    if all(
        check.passed
        for check in threshold_checks
    ):
        status = EvaluationStatus.PASS
    else:
        status = EvaluationStatus.FAIL

    return EvaluationResult(
        status=status,
        checks=tuple(
            validity_checks + threshold_checks
        ),
    )