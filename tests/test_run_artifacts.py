from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ai_performance_lab.runs import (
    RunArtifactExistsError,
    RunDirectoryExistsError,
    create_run_artifacts,
    generate_run_id,
    stage_run_inputs,
    write_run_manifest,
)


def test_generate_run_ids_are_unique() -> None:
    run_ids = {
        generate_run_id()
        for _ in range(100)
    }

    assert len(run_ids) == 100

    for run_id in run_ids:
        assert re.fullmatch(
            r"RUN-\d{8}T\d{12}Z-[0-9a-f]{8}",
            run_id,
        )


def test_consecutive_run_directories_do_not_conflict(
    tmp_path: Path,
) -> None:
    artifacts = [
        create_run_artifacts(tmp_path)
        for _ in range(100)
    ]

    run_ids = {
        item.run_id
        for item in artifacts
    }
    directories = {
        item.directory
        for item in artifacts
    }

    assert len(run_ids) == 100
    assert len(directories) == 100
    assert all(path.is_dir() for path in directories)


def test_existing_run_directory_is_not_reused(
    tmp_path: Path,
) -> None:
    fixed_run_id = generate_run_id(
        now=datetime(
            2026,
            9,
            4,
            8,
            30,
            15,
            123456,
            tzinfo=timezone.utc,
        ),
        suffix="abcdef12",
    )

    first_run = create_run_artifacts(
        tmp_path,
        run_id=fixed_run_id,
    )

    sentinel_path = first_run.directory / "sentinel.txt"
    sentinel_path.write_text(
        "original evidence",
        encoding="utf-8",
    )

    with pytest.raises(RunDirectoryExistsError):
        create_run_artifacts(
            tmp_path,
            run_id=fixed_run_id,
        )

    assert sentinel_path.read_text(
        encoding="utf-8"
    ) == "original evidence"


def test_staged_inputs_are_not_overwritten(
    tmp_path: Path,
) -> None:
    spec_source = tmp_path / "source.yaml"
    plan_source = tmp_path / "source.jmx"
    properties_source = tmp_path / "source.properties"

    spec_source.write_text(
        'version: "1.0"\n',
        encoding="utf-8",
    )
    plan_source.write_text(
        "<jmeterTestPlan />\n",
        encoding="utf-8",
    )
    properties_source.write_text(
        "jmeter.save.saveservice.output_format=csv\n",
        encoding="utf-8",
    )

    artifacts = create_run_artifacts(tmp_path / "runs")

    stage_run_inputs(
        artifacts=artifacts,
        test_spec_source=spec_source,
        test_plan_source=plan_source,
        result_properties_source=properties_source,
    )

    original_spec = artifacts.test_spec_path.read_text(
        encoding="utf-8"
    )

    spec_source.write_text(
        'version: "changed"\n',
        encoding="utf-8",
    )

    with pytest.raises(RunArtifactExistsError):
        stage_run_inputs(
            artifacts=artifacts,
            test_spec_source=spec_source,
            test_plan_source=plan_source,
            result_properties_source=properties_source,
        )

    assert artifacts.test_spec_path.read_text(
        encoding="utf-8"
    ) == original_spec


def test_run_manifest_is_immutable(
    tmp_path: Path,
) -> None:
    artifacts = create_run_artifacts(tmp_path)

    write_run_manifest(
        artifacts,
        status="SUCCESS",
        details={"exit_code": 0},
    )

    manifest_before = json.loads(
        artifacts.manifest_path.read_text(encoding="utf-8")
    )

    with pytest.raises(RunArtifactExistsError):
        write_run_manifest(
            artifacts,
            status="FAILED",
            details={"exit_code": 1},
        )

    manifest_after = json.loads(
        artifacts.manifest_path.read_text(encoding="utf-8")
    )

    assert manifest_after == manifest_before
    assert manifest_after["run_id"] == artifacts.run_id
    assert manifest_after["status"] == "SUCCESS"