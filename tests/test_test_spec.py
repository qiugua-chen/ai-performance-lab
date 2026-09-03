from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml

from ai_performance_lab.test_spec import (
    TestSpecError,
    load_test_spec,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALID_SPEC_PATH = (
    PROJECT_ROOT
    / "examples"
    / "test_specs"
    / "normal.yaml"
)

VALID_SPEC: dict[str, Any] = {
    "version": "1.0",
    "name": "demo-normal-api",
    "request": {
        "method": "GET",
        "url": "http://127.0.0.1:8001/api/normal",
    },
    "load": {
        "threads": 10,
        "ramp_up_seconds": 5,
        "duration_seconds": 60,
    },
    "acceptance": {
        "min_rps": 1.0,
        "min_samples": 10,
        "p95_ms": 500.0,
        "success_rate": 99.9,
    },
}


def write_spec(
    tmp_path: Path,
    spec_data: Any,
) -> Path:
    spec_path = tmp_path / "test-spec.yaml"
    spec_path.write_text(
        yaml.safe_dump(spec_data, sort_keys=False),
        encoding="utf-8",
    )
    return spec_path


def test_loads_valid_test_spec() -> None:
    test_spec = load_test_spec(VALID_SPEC_PATH)

    assert test_spec.version == "1.0"
    assert test_spec.name == "demo-normal-api"
    assert test_spec.request.method == "GET"
    assert test_spec.load.threads == 10
    assert test_spec.acceptance.p95_ms == 500.0


def test_rejects_missing_required_section(
    tmp_path: Path,
) -> None:
    invalid_spec = deepcopy(VALID_SPEC)
    del invalid_spec["request"]

    with pytest.raises(TestSpecError):
        load_test_spec(write_spec(tmp_path, invalid_spec))


def test_rejects_unknown_field(
    tmp_path: Path,
) -> None:
    invalid_spec = deepcopy(VALID_SPEC)
    invalid_spec["unexpected"] = "not allowed"

    with pytest.raises(TestSpecError):
        load_test_spec(write_spec(tmp_path, invalid_spec))


def test_rejects_unsupported_method(
    tmp_path: Path,
) -> None:
    invalid_spec = deepcopy(VALID_SPEC)
    invalid_spec["request"]["method"] = "POST"

    with pytest.raises(TestSpecError):
        load_test_spec(write_spec(tmp_path, invalid_spec))


def test_rejects_zero_threads(
    tmp_path: Path,
) -> None:
    invalid_spec = deepcopy(VALID_SPEC)
    invalid_spec["load"]["threads"] = 0

    with pytest.raises(TestSpecError):
        load_test_spec(write_spec(tmp_path, invalid_spec))


def test_rejects_ramp_up_longer_than_duration(
    tmp_path: Path,
) -> None:
    invalid_spec = deepcopy(VALID_SPEC)
    invalid_spec["load"]["ramp_up_seconds"] = 61

    with pytest.raises(TestSpecError):
        load_test_spec(write_spec(tmp_path, invalid_spec))


def test_rejects_invalid_success_rate(
    tmp_path: Path,
) -> None:
    invalid_spec = deepcopy(VALID_SPEC)
    invalid_spec["acceptance"]["success_rate"] = 100.1

    with pytest.raises(TestSpecError):
        load_test_spec(write_spec(tmp_path, invalid_spec))


def test_rejects_non_mapping_root(
    tmp_path: Path,
) -> None:
    invalid_spec = ["not", "a", "mapping"]

    with pytest.raises(TestSpecError):
        load_test_spec(write_spec(tmp_path, invalid_spec))