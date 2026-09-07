from __future__ import annotations

from math import ceil, fsum
from typing import Sequence

from ai_performance_lab.jtl import JTLSample
from ai_performance_lab.metrics.models import PerformanceMetrics


class MetricsCalculationError(RuntimeError):
    """确定性指标计算失败的异常基类。"""


class MetricsEmptyError(MetricsCalculationError):
    """没有可用样本时抛出此异常。"""


class MetricsInvalidWindowError(MetricsCalculationError):
    """观测到的执行时间窗口时长不为正值时抛出此异常。"""


def nearest_rank_percentile(
    values: Sequence[int],
    percentile: float,
) -> int:
    """使用最近秩法（nearest-rank）计算指定百分位数。"""

    if not values:
        raise MetricsEmptyError(
            "Cannot calculate a percentile from an empty dataset."
        )

    if not 0 < percentile <= 100:
        raise ValueError(
            "Percentile must be greater than 0 and no greater than 100."
        )

    sorted_values = sorted(values)
    rank = ceil((percentile / 100) * len(sorted_values))
    index = max(rank - 1, 0)

    return sorted_values[index]


def calculate_metrics(
    samples: Sequence[JTLSample],
) -> PerformanceMetrics:
    """根据已校验的 JTL 样本计算确定性的 M0 指标。"""

    if not samples:
        raise MetricsEmptyError(
            "Cannot calculate metrics because the JTL has no samples."
        )

    request_count = len(samples)

    success_count = sum(
        1
        for sample in samples
        if sample.success
    )
    error_count = request_count - success_count

    earliest_start_ms = min(
        sample.timestamp_ms
        for sample in samples
    )
    latest_end_ms = max(
        sample.timestamp_ms + sample.elapsed_ms
        for sample in samples
    )

    duration_ms = latest_end_ms - earliest_start_ms

    if duration_ms <= 0:
        raise MetricsInvalidWindowError(
            "The JTL execution window must be greater than zero."
        )

    duration_seconds = duration_ms / 1000
    elapsed_values = [
        sample.elapsed_ms
        for sample in samples
    ]

    return PerformanceMetrics(
        request_count=request_count,
        success_count=success_count,
        error_count=error_count,
        duration_seconds=round(duration_seconds, 6),
        rps=round(request_count / duration_seconds, 6),
        success_rate=round(
            success_count / request_count,
            6,
        ),
        error_rate=round(
            error_count / request_count,
            6,
        ),
        min_ms=min(elapsed_values),
        avg_ms=round(
            fsum(elapsed_values) / request_count,
            6,
        ),
        max_ms=max(elapsed_values),
        p50_ms=nearest_rank_percentile(
            elapsed_values,
            50,
        ),
        p90_ms=nearest_rank_percentile(
            elapsed_values,
            90,
        ),
        p95_ms=nearest_rank_percentile(
            elapsed_values,
            95,
        ),
        p99_ms=nearest_rank_percentile(
            elapsed_values,
            99,
        ),
    )