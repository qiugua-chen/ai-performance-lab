from __future__ import annotations

import os
import shutil
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Sequence

from ai_performance_lab.test_spec.models import TestSpec


class JMeterExecutionError(RuntimeError):
    """Base exception for JMeter execution failures."""


class JMeterCommandNotFoundError(JMeterExecutionError):
    """Raised when the configured JMeter command does not exist."""


class JMeterTimeoutError(JMeterExecutionError):
    """Raised when JMeter exceeds the configured timeout."""

    def __init__(self, timeout_seconds: float) -> None:
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"JMeter exceeded the timeout of {timeout_seconds} seconds."
        )


class JMeterProcessError(JMeterExecutionError):
    """Raised when JMeter exits with a non-zero status."""

    def __init__(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
    ) -> None:
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(f"JMeter exited with status {exit_code}.")


class JMeterOutputError(JMeterExecutionError):
    """Raised when expected JMeter output files are missing."""


@dataclass(frozen=True)
class JMeterExecutionResult:
    """Successful JMeter execution result."""

    command: tuple[str, ...]
    exit_code: int
    elapsed_seconds: float
    stdout: str
    stderr: str
    jtl_path: Path
    log_path: Path


def resolve_jmeter_command(command: str | Path) -> Path:
    """Resolve an explicit path or a command available on PATH."""

    command_text = str(command)
    explicit_path = Path(command_text).expanduser()

    if explicit_path.is_file():
        return explicit_path.resolve()

    discovered_path = shutil.which(command_text)

    if discovered_path is not None:
        return Path(discovered_path).resolve()

    raise JMeterCommandNotFoundError(
        f"JMeter command was not found: {command_text}"
    )


def build_jmeter_command(
    spec: TestSpec,
    jmeter_command: str | Path,
    template_path: str | Path,
    result_properties_path: str | Path,
    jtl_path: str | Path,
    log_path: str | Path,
    connect_timeout_ms: int = 5000,
    response_timeout_ms: int = 10000,
    expected_status: int = 200,
) -> list[str]:
    """Translate a Test Spec into a deterministic JMeter command."""

    resolved_jmeter = resolve_jmeter_command(jmeter_command)
    resolved_template = Path(template_path).resolve()
    resolved_properties = Path(result_properties_path).resolve()

    if not resolved_template.is_file():
        raise JMeterExecutionError(
            f"JMeter template does not exist: {resolved_template}"
        )

    if not resolved_properties.is_file():
        raise JMeterExecutionError(
            f"JTL properties file does not exist: {resolved_properties}"
        )

    request_url = spec.request.url
    request_path = request_url.path or "/"

    if request_url.query:
        request_path = f"{request_path}?{request_url.query}"

    request_port = request_url.port

    if request_port is None:
        request_port = 443 if request_url.scheme == "https" else 80

    properties = {
        "threads": spec.load.threads,
        "ramp_up_seconds": spec.load.ramp_up_seconds,
        "duration_seconds": spec.load.duration_seconds,
        "protocol": request_url.scheme,
        "host": request_url.host,
        "port": request_port,
        "path": request_path,
        "connect_timeout_ms": connect_timeout_ms,
        "response_timeout_ms": response_timeout_ms,
        "expected_status": expected_status,
    }

    command = [
        str(resolved_jmeter),
        "-n",
        "-t",
        str(resolved_template),
        "-q",
        str(resolved_properties),
        "-l",
        str(Path(jtl_path).resolve()),
        "-j",
        str(Path(log_path).resolve()),
    ]

    for name, value in properties.items():
        command.append(f"-J{name}={value}")

    return command


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    """Terminate JMeter and child processes after a timeout."""

    if os.name == "nt":
        subprocess.run(
            [
                "taskkill",
                "/PID",
                str(process.pid),
                "/T",
                "/F",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return

    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
    except ProcessLookupError:
        return
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)


def execute_jmeter(
    spec: TestSpec,
    jmeter_command: str | Path,
    template_path: str | Path,
    result_properties_path: str | Path,
    jtl_path: str | Path,
    log_path: str | Path,
    timeout_seconds: float,
) -> JMeterExecutionResult:
    """Execute JMeter and return a successful result or typed exception."""

    resolved_jtl = Path(jtl_path).resolve()
    resolved_log = Path(log_path).resolve()

    if resolved_jtl == resolved_log:
        raise JMeterOutputError(
            "JTL path and JMeter log path must be different."
        )

    for output_path in (resolved_jtl, resolved_log):
        if output_path.exists():
            raise JMeterOutputError(
                f"Refusing to overwrite existing output: {output_path}"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

    command = build_jmeter_command(
        spec=spec,
        jmeter_command=jmeter_command,
        template_path=template_path,
        result_properties_path=result_properties_path,
        jtl_path=resolved_jtl,
        log_path=resolved_log,
    )

    process_options: dict[str, object] = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "errors": "replace",
        "shell": False,
    }

    if os.name == "nt":
        process_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        process_options["start_new_session"] = True

    started_at = perf_counter()

    try:
        process = subprocess.Popen(
            command,
            **process_options,
        )
    except FileNotFoundError as error:
        raise JMeterCommandNotFoundError(
            f"JMeter command was not found: {command[0]}"
        ) from error
    except OSError as error:
        raise JMeterExecutionError(
            f"JMeter could not be started: {error}"
        ) from error

    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as error:
        _terminate_process_tree(process)
        process.communicate()

        raise JMeterTimeoutError(timeout_seconds) from error

    elapsed_seconds = perf_counter() - started_at

    if process.returncode != 0:
        raise JMeterProcessError(
            exit_code=process.returncode,
            stdout=stdout,
            stderr=stderr,
        )

    missing_outputs = [
        output_path
        for output_path in (resolved_jtl, resolved_log)
        if not output_path.is_file()
    ]

    if missing_outputs:
        missing_text = ", ".join(str(path) for path in missing_outputs)
        raise JMeterOutputError(
            f"JMeter completed but expected outputs are missing: {missing_text}"
        )

    return JMeterExecutionResult(
        command=tuple(command),
        exit_code=process.returncode,
        elapsed_seconds=elapsed_seconds,
        stdout=stdout,
        stderr=stderr,
        jtl_path=resolved_jtl,
        log_path=resolved_log,
    )