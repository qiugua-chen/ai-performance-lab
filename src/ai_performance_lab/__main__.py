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
        description="AI Performance Lab M0 执行与评估工作流。"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    run_parser = subparsers.add_parser(
        "run",
        help="执行一次完整的 M0 工作流。",
    )

    run_parser.add_argument(
        "--spec",
        required=True,
        help="YAML 测试规格文件的路径。",
    )
    run_parser.add_argument(
        "--jmeter",
        required=True,
        help="jmeter.bat、jmeter 的路径，或 PATH 中可用的命令。",
    )
    run_parser.add_argument(
        "--template",
        default="jmeter/templates/http_get.jmx",
        help="固定的 JMeter 模板文件路径。",
    )
    run_parser.add_argument(
        "--result-properties",
        default="jmeter/config/jtl-save.properties",
        help="固定的 JTL 输出配置文件路径。",
    )
    run_parser.add_argument(
        "--runs-root",
        default="runs",
        help="用于保存独立运行产物的根目录。",
    )
    run_parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30,
        help="JMeter 执行超时时限，单位为秒。",
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