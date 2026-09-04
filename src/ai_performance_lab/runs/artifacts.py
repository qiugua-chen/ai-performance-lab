from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


RUN_ID_PATTERN = re.compile(
    r"^RUN-\d{8}T\d{12}Z-[0-9a-f]{8}$"
)


class RunArtifactError(RuntimeError):
    """Base exception for Run identity and artifact failures."""


class RunDirectoryExistsError(RunArtifactError):
    """Raised when a Run directory already exists."""


class RunArtifactExistsError(RunArtifactError):
    """Raised when an artifact would be overwritten."""


class RunSourceNotFoundError(RunArtifactError):
    """Raised when a source artifact does not exist."""


@dataclass(frozen=True)
class RunArtifacts:
    """Paths belonging exclusively to one performance Run."""

    run_id: str
    created_at_utc: str
    directory: Path
    test_spec_path: Path
    test_plan_path: Path
    result_properties_path: Path
    jtl_path: Path
    jmeter_log_path: Path
    manifest_path: Path


def generate_run_id(
    now: datetime | None = None,
    suffix: str | None = None,
) -> str:
    """Generate a sortable and collision-resistant Run ID."""

    instant = now or datetime.now(timezone.utc)

    if instant.tzinfo is None:
        raise ValueError("Run ID datetime must include timezone information.")

    utc_instant = instant.astimezone(timezone.utc)
    timestamp = utc_instant.strftime("%Y%m%dT%H%M%S%fZ")
    unique_suffix = suffix or uuid4().hex[:8]

    if not re.fullmatch(r"[0-9a-f]{8}", unique_suffix):
        raise ValueError(
            "Run ID suffix must contain exactly 8 lowercase hexadecimal characters."
        )

    return f"RUN-{timestamp}-{unique_suffix}"


def create_run_artifacts(
    runs_root: str | Path = "runs",
    run_id: str | None = None,
) -> RunArtifacts:
    """Atomically create an isolated directory for one Run."""

    created_at = datetime.now(timezone.utc)
    selected_run_id = run_id or generate_run_id(created_at)

    if RUN_ID_PATTERN.fullmatch(selected_run_id) is None:
        raise ValueError(f"Invalid Run ID: {selected_run_id}")

    root_directory = Path(runs_root).resolve()
    root_directory.mkdir(parents=True, exist_ok=True)

    run_directory = root_directory / selected_run_id

    try:
        run_directory.mkdir(exist_ok=False)
    except FileExistsError as error:
        raise RunDirectoryExistsError(
            f"Run directory already exists and will not be reused: "
            f"{run_directory}"
        ) from error

    return RunArtifacts(
        run_id=selected_run_id,
        created_at_utc=created_at.isoformat(),
        directory=run_directory,
        test_spec_path=run_directory / "test-spec.yaml",
        test_plan_path=run_directory / "test-plan.jmx",
        result_properties_path=(
            run_directory / "jtl-save.properties"
        ),
        jtl_path=run_directory / "result.jtl",
        jmeter_log_path=run_directory / "jmeter.log",
        manifest_path=run_directory / "run.json",
    )


def _copy_file_without_overwrite(
    source: str | Path,
    destination: Path,
) -> None:
    """Copy one file while refusing to replace an existing destination."""

    source_path = Path(source).resolve()

    if not source_path.is_file():
        raise RunSourceNotFoundError(
            f"Run source file does not exist: {source_path}"
        )

    try:
        with (
            source_path.open("rb") as source_file,
            destination.open("xb") as destination_file,
        ):
            shutil.copyfileobj(source_file, destination_file)
    except FileExistsError as error:
        raise RunArtifactExistsError(
            f"Run artifact already exists and will not be overwritten: "
            f"{destination}"
        ) from error


def stage_run_inputs(
    artifacts: RunArtifacts,
    test_spec_source: str | Path,
    test_plan_source: str | Path,
    result_properties_source: str | Path,
) -> None:
    """Copy the exact execution inputs into the Run directory."""

    _copy_file_without_overwrite(
        test_spec_source,
        artifacts.test_spec_path,
    )
    _copy_file_without_overwrite(
        test_plan_source,
        artifacts.test_plan_path,
    )
    _copy_file_without_overwrite(
        result_properties_source,
        artifacts.result_properties_path,
    )


def write_run_manifest(
    artifacts: RunArtifacts,
    status: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Write the final immutable metadata file for one Run."""

    manifest = {
        "schema_version": "1.0",
        "run_id": artifacts.run_id,
        "status": status,
        "created_at_utc": artifacts.created_at_utc,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            "test_spec": artifacts.test_spec_path.name,
            "test_plan": artifacts.test_plan_path.name,
            "result_properties": artifacts.result_properties_path.name,
            "jtl": artifacts.jtl_path.name,
            "jmeter_log": artifacts.jmeter_log_path.name,
        },
        "details": details or {},
    }

    try:
        with artifacts.manifest_path.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as manifest_file:
            json.dump(
                manifest,
                manifest_file,
                ensure_ascii=False,
                indent=2,
            )
            manifest_file.write("\n")
    except FileExistsError as error:
        raise RunArtifactExistsError(
            f"Run manifest already exists and will not be overwritten: "
            f"{artifacts.manifest_path}"
        ) from error