from __future__ import annotations

import argparse

from ai_performance_lab.executors import JMeterExecutionError
from ai_performance_lab.jtl import JTLParseError
from ai_performance_lab.metrics import (
    MetricsCalculationError,
    MetricsOutputError,
)
from ai_performance_lab.pipeline import run_m0_pipeline
from ai_performance_lab.rules import (
    EvaluationOutputError,
    EvaluationStatus,
)
from ai_performance_lab.runs import RunArtifactError
from ai_performance_lab.test_spec.loader import TestSpecError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI Performance Lab deterministic M0 workflow."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Execute one complete deterministic M0 Run.",
    )

    run_parser.add_argument(
        "--spec",
        required=True,
        help="Path to the Test Spec YAML file.",
    )
    run_parser.add_argument(
        "--jmeter",
        required=True,
        help="Path to jmeter.bat, jmeter, or a command on PATH.",
    )
    run_parser.add_argument(
        "--template",
        default="jmeter/templates/http_get.jmx",
        help="Path to the deterministic JMeter template.",
    )
    run_parser.add_argument(
        "--result-properties",
        default="jmeter/config/jtl-save.properties",
        help="Path to the fixed JTL properties file.",
    )
    run_parser.add_argument(
        "--runs-root",
        default="runs",
        help="Root directory for isolated Run artifacts.",
    )
    run_parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30,
        help="Maximum JMeter execution time.",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command != "run":
        return 10

    try:
        result = run_m0_pipeline(
            spec_path=args.spec,
            jmeter_command=args.jmeter,
            template_path=args.template,
            result_properties_path=args.result_properties,
            runs_root=args.runs_root,
            timeout_seconds=args.timeout_seconds,
        )

    except (
        TestSpecError,
        JMeterExecutionError,
        JTLParseError,
        MetricsCalculationError,
        MetricsOutputError,
        EvaluationOutputError,
        RunArtifactError,
        OSError,
        ValueError,
    ) as error:
        print("PIPELINE_ERROR")
        print(f"error_type={type(error).__name__}")
        print(f"error={error}")
        return 10

    print(f"run_id={result.artifacts.run_id}")
    print(f"run_directory={result.artifacts.directory}")
    print(f"sample_count={result.metrics.request_count}")
    print(f"rps={result.metrics.rps}")
    print(f"p95_ms={result.metrics.p95_ms}")
    print(f"success_rate={result.metrics.success_rate}")
    print(f"status={result.evaluation.status.value}")
    print(
        "failed_checks="
        + ",".join(
            check.name
            for check in result.evaluation.failed_checks
        )
    )

    if result.evaluation.status is EvaluationStatus.PASS:
        return 0

    if result.evaluation.status is EvaluationStatus.FAIL:
        return 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())