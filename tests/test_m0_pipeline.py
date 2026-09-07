from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ai_performance_lab.pipeline import run_m0_pipeline
from ai_performance_lab.rules import EvaluationStatus


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FIXED_JTL_PATH = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "jtl"
    / "fixed-metrics.jtl"
)

TEMPLATE_PATH = (
    PROJECT_ROOT
    / "jmeter"
    / "templates"
    / "http_get.jmx"
)

PROPERTIES_PATH = (
    PROJECT_ROOT
    / "jmeter"
    / "config"
    / "jtl-save.properties"
)


@pytest.mark.parametrize(
    ("spec_name", "expected_status"),
    [
        ("rule-pass.yaml", EvaluationStatus.PASS),
        ("rule-fail.yaml", EvaluationStatus.FAIL),
        ("rule-invalid.yaml", EvaluationStatus.INVALID),
    ],
)
def test_pipeline_creates_complete_artifacts(
    tmp_path: Path,
    spec_name: str,
    expected_status: EvaluationStatus,
) -> None:
    spec_path = (
        PROJECT_ROOT
        / "tests"
        / "fixtures"
        / "test_specs"
        / spec_name
    )

    def fake_execute_jmeter(**kwargs):
        shutil.copyfile(
            FIXED_JTL_PATH,
            kwargs["jtl_path"],
        )

        Path(kwargs["log_path"]).write_text(
            "Fake JMeter execution completed.\n",
            encoding="utf-8",
        )

        return SimpleNamespace(
            exit_code=0,
            elapsed_seconds=0.1,
        )

    with patch(
        "ai_performance_lab.pipeline.execute_jmeter",
        side_effect=fake_execute_jmeter,
    ):
        result = run_m0_pipeline(
            spec_path=spec_path,
            jmeter_command="unused-in-test",
            template_path=TEMPLATE_PATH,
            result_properties_path=PROPERTIES_PATH,
            runs_root=tmp_path / "runs",
            timeout_seconds=30,
        )

    assert result.evaluation.status is expected_status

    assert result.artifacts.test_spec_path.is_file()
    assert result.artifacts.test_plan_path.is_file()
    assert result.artifacts.result_properties_path.is_file()
    assert result.artifacts.jtl_path.is_file()
    assert result.artifacts.jmeter_log_path.is_file()
    assert result.artifacts.metrics_path.is_file()
    assert result.artifacts.evaluation_path.is_file()
    assert result.artifacts.manifest_path.is_file()

    manifest = json.loads(
        result.artifacts.manifest_path.read_text(
            encoding="utf-8"
        )
    )

    assert manifest["run_id"] == result.artifacts.run_id
    assert manifest["status"] == expected_status.value