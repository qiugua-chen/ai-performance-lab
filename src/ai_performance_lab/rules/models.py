from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class EvaluationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INVALID = "INVALID"


@dataclass(frozen=True)
class RuleCheck:
    """Result of one deterministic rule check."""

    name: str
    category: str
    actual: int | float
    operator: str
    expected: int | float
    passed: bool
    message: str


@dataclass(frozen=True)
class EvaluationResult:
    """Final deterministic evaluation result."""

    status: EvaluationStatus
    checks: tuple[RuleCheck, ...]

    @property
    def failed_checks(self) -> tuple[RuleCheck, ...]:
        return tuple(
            check
            for check in self.checks
            if not check.passed
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "checks": [
                asdict(check)
                for check in self.checks
            ],
            "failed_checks": [
                check.name
                for check in self.failed_checks
            ],
        }