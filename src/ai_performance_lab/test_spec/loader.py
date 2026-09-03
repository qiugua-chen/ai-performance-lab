from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from ai_performance_lab.test_spec.models import TestSpec


class TestSpecError(ValueError):
    """Raised when a Test Spec file cannot be loaded or validated."""


def load_test_spec(path: str | Path) -> TestSpec:
    """Load and validate a Test Spec YAML file."""

    spec_path = Path(path)

    try:
        raw_content = spec_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise TestSpecError(
            f"Test Spec file not found: {spec_path}"
        ) from exc
    except OSError as exc:
        raise TestSpecError(
            f"Test Spec file cannot be read: {spec_path}"
        ) from exc

    try:
        raw_data: Any = yaml.safe_load(raw_content)
    except yaml.YAMLError as exc:
        raise TestSpecError(
            f"Invalid YAML syntax in: {spec_path}"
        ) from exc

    if not isinstance(raw_data, dict):
        raise TestSpecError(
            "Test Spec root must be a YAML mapping"
        )

    try:
        return TestSpec.model_validate(raw_data)
    except ValidationError as exc:
        raise TestSpecError(
            f"Test Spec validation failed:\n{exc}"
        ) from exc