from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PerformanceMetrics:
    """Deterministic metrics calculated from validated JTL samples."""

    request_count: int
    success_count: int
    error_count: int

    duration_seconds: float
    rps: float

    success_rate: float
    error_rate: float

    min_ms: int
    avg_ms: float
    max_ms: int

    p50_ms: int
    p90_ms: int
    p95_ms: int
    p99_ms: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)