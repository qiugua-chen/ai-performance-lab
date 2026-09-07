from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_performance_lab.executors import execute_jmeter
from ai_performance_lab.jtl import parse_jtl
from ai_performance_lab.metrics import (
    PerformanceMetrics,
    calculate_metrics,
    write_metrics_json,
)
from ai_performance_lab.rules import (
    EvaluationResult,
    evaluate_metrics,
    write_evaluation_json,
)
from ai_performance_lab.runs import (
    RunArtifactError,
    RunArtifacts,
    create_run_artifacts,
    stage_run_inputs,
    write_run_manifest,
)
from ai_performance_lab.test_spec.loader import load_test_spec


@dataclass(frozen=True)
class M0PipelineResult:
    """Completed M0 pipeline result."""

    artifacts: RunArtifacts
    metrics: PerformanceMetrics
    evaluation: EvaluationResult
    executor_exit_code: int
    executor_elapsed_seconds: float


def run_m0_pipeline(
    spec_path: str | Path,
    jmeter_command: str | Path,
    template_path: str | Path,
    result_properties_path: str | Path,
    runs_root: str | Path,
    timeout_seconds: float,
) -> M0PipelineResult:
    """Run the complete deterministic M0 workflow."""

    artifacts = create_run_artifacts(runs_root)

    try:
        stage_run_inputs(
            artifacts=artifacts,
            test_spec_source=spec_path,
            test_plan_source=template_path,
            result_properties_source=result_properties_path,
        )

        spec = load_test_spec(artifacts.test_spec_path)

        execution = execute_jmeter(
            spec=spec,
            jmeter_command=jmeter_command,
            template_path=artifacts.test_plan_path,
            result_properties_path=artifacts.result_properties_path,
            jtl_path=artifacts.jtl_path,
            log_path=artifacts.jmeter_log_path,
            timeout_seconds=timeout_seconds,
        )

        document = parse_jtl(artifacts.jtl_path)

        metrics = calculate_metrics(document.samples)

        write_metrics_json(
            metrics,
            artifacts.metrics_path,
        )

        evaluation = evaluate_metrics(
            metrics,
            spec,
        )

        write_evaluation_json(
            evaluation,
            artifacts.evaluation_path,
        )

        write_run_manifest(
            artifacts,
            status=evaluation.status.value,
            details={
                "executor_exit_code": execution.exit_code,
                "executor_elapsed_seconds": round(
                    execution.elapsed_seconds,
                    3,
                ),
                "sample_count": document.sample_count,
                "evaluation_status": evaluation.status.value,
            },
        )

    except Exception as error:
        if not artifacts.manifest_path.exists():
            try:
                write_run_manifest(
                    artifacts,
                    status="ERROR",
                    details={
                        "error_type": type(error).__name__,
                        "error": str(error),
                    },
                )
            except RunArtifactError:
                pass

        raise

    return M0PipelineResult(
        artifacts=artifacts,
        metrics=metrics,
        evaluation=evaluation,
        executor_exit_code=execution.exit_code,
        executor_elapsed_seconds=execution.elapsed_seconds,
    )