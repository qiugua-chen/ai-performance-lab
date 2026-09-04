from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ai_performance_lab.executors import (
    JMeterCommandNotFoundError,
    JMeterProcessError,
    JMeterTimeoutError,
    execute_jmeter,
)
from ai_performance_lab.test_spec.loader import load_test_spec


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMOKE_SPEC_PATH = PROJECT_ROOT / "examples/test_specs/smoke.yaml"


def create_executor_inputs(
    tmp_path: Path,
) -> tuple[Path, Path, Path, Path]:
    jmeter_command = tmp_path / "jmeter.bat"
    template_path = tmp_path / "http_get.jmx"
    properties_path = tmp_path / "jtl-save.properties"
    output_directory = tmp_path / "run"

    jmeter_command.write_text("@echo off\n", encoding="utf-8")
    template_path.write_text("<jmeterTestPlan />\n", encoding="utf-8")
    properties_path.write_text(
        "jmeter.save.saveservice.output_format=csv\n",
        encoding="utf-8",
    )

    return (
        jmeter_command,
        template_path,
        properties_path,
        output_directory,
    )


def test_execute_jmeter_returns_success_result(
    tmp_path: Path,
) -> None:
    (
        jmeter_command,
        template_path,
        properties_path,
        output_directory,
    ) = create_executor_inputs(tmp_path)

    jtl_path = output_directory / "results.jtl"
    log_path = output_directory / "jmeter.log"
    spec = load_test_spec(SMOKE_SPEC_PATH)

    fake_process = Mock()
    fake_process.pid = 12345
    fake_process.returncode = 0

    def complete_process(
        timeout: float,
    ) -> tuple[str, str]:
        jtl_path.write_text(
            "timeStamp,elapsed,label,responseCode,success\n",
            encoding="utf-8",
        )
        log_path.write_text("JMeter finished\n", encoding="utf-8")
        return "summary = 1 in 00:00:03", ""

    fake_process.communicate.side_effect = complete_process

    with patch(
        "ai_performance_lab.executors.jmeter.subprocess.Popen",
        return_value=fake_process,
    ):
        result = execute_jmeter(
            spec=spec,
            jmeter_command=jmeter_command,
            template_path=template_path,
            result_properties_path=properties_path,
            jtl_path=jtl_path,
            log_path=log_path,
            timeout_seconds=30,
        )

    assert result.exit_code == 0
    assert result.jtl_path == jtl_path.resolve()
    assert result.log_path == log_path.resolve()
    assert "-Jthreads=1" in result.command
    assert "-Jduration_seconds=3" in result.command
    assert "-Jpath=/api/normal" in result.command


def test_execute_jmeter_recognizes_timeout(
    tmp_path: Path,
) -> None:
    (
        jmeter_command,
        template_path,
        properties_path,
        output_directory,
    ) = create_executor_inputs(tmp_path)

    spec = load_test_spec(SMOKE_SPEC_PATH)

    fake_process = Mock()
    fake_process.pid = 12345
    fake_process.communicate.side_effect = [
        subprocess.TimeoutExpired(cmd="jmeter", timeout=1),
        ("", ""),
    ]

    with (
        patch(
            "ai_performance_lab.executors.jmeter.subprocess.Popen",
            return_value=fake_process,
        ),
        patch(
            "ai_performance_lab.executors.jmeter._terminate_process_tree"
        ) as terminate_process_tree,
        pytest.raises(JMeterTimeoutError),
    ):
        execute_jmeter(
            spec=spec,
            jmeter_command=jmeter_command,
            template_path=template_path,
            result_properties_path=properties_path,
            jtl_path=output_directory / "results.jtl",
            log_path=output_directory / "jmeter.log",
            timeout_seconds=1,
        )

    terminate_process_tree.assert_called_once_with(fake_process)


def test_execute_jmeter_recognizes_missing_command(
    tmp_path: Path,
) -> None:
    spec = load_test_spec(SMOKE_SPEC_PATH)
    missing_command = tmp_path / "missing" / "jmeter.bat"

    with pytest.raises(JMeterCommandNotFoundError):
        execute_jmeter(
            spec=spec,
            jmeter_command=missing_command,
            template_path=PROJECT_ROOT / "jmeter/templates/http_get.jmx",
            result_properties_path=(
                PROJECT_ROOT / "jmeter/config/jtl-save.properties"
            ),
            jtl_path=tmp_path / "results.jtl",
            log_path=tmp_path / "jmeter.log",
            timeout_seconds=30,
        )


def test_execute_jmeter_recognizes_nonzero_exit(
    tmp_path: Path,
) -> None:
    (
        jmeter_command,
        template_path,
        properties_path,
        output_directory,
    ) = create_executor_inputs(tmp_path)

    spec = load_test_spec(SMOKE_SPEC_PATH)

    fake_process = Mock()
    fake_process.pid = 12345
    fake_process.returncode = 1
    fake_process.communicate.return_value = (
        "",
        "JMeter execution failed",
    )

    with (
        patch(
            "ai_performance_lab.executors.jmeter.subprocess.Popen",
            return_value=fake_process,
        ),
        pytest.raises(JMeterProcessError) as captured_error,
    ):
        execute_jmeter(
            spec=spec,
            jmeter_command=jmeter_command,
            template_path=template_path,
            result_properties_path=properties_path,
            jtl_path=output_directory / "results.jtl",
            log_path=output_directory / "jmeter.log",
            timeout_seconds=30,
        )

    assert captured_error.value.exit_code == 1