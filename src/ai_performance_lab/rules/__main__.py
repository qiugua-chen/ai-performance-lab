from __future__ import annotations

import argparse
import json
from dataclasses import fields
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from ai_performance_lab.metrics import PerformanceMetrics
from ai_performance_lab.rules import (
    EvaluationOutputError,
    EvaluationStatus,
    evaluate_metrics,
    write_evaluation_json,
)
from ai_performance_lab.test_spec.loader import (
    TestSpecError,
    load_test_spec,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "依据测试规格评估性能指标。"
        )
    )

    parser.add_argument(
        "--spec",
        required=True,
        help="YAML 测试规格文件的路径。",
    )
    parser.add_argument(
        "--metrics",
        required=True,
        help="metrics.json 文件路径。",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="evaluation.json 输出路径，目标文件必须尚不存在。",
    )

    return parser


def load_metrics_json(
    path: str | Path,
) -> PerformanceMetrics:
    metrics_path = Path(path).resolve()

    if not metrics_path.is_file():
        raise ValueError(
            f"Metrics file does not exist: {metrics_path}"
        )

    with metrics_path.open(
        "r",
        encoding="utf-8-sig",
    ) as metrics_file:
        payload: dict[str, Any] = json.load(
            metrics_file
        )

    metric_names = {
        field.name
        for field in fields(PerformanceMetrics)
    }

    missing_fields = metric_names.difference(
        payload.keys()
    )
    unexpected_fields = (
        set(payload.keys())
        .difference(metric_names)
        .difference({"schema_version"})
    )

    if missing_fields:
        missing_text = ", ".join(
            sorted(missing_fields)
        )
        raise ValueError(
            f"Metrics file is missing fields: {missing_text}"
        )

    if unexpected_fields:
        unexpected_text = ", ".join(
            sorted(unexpected_fields)
        )
        raise ValueError(
            f"Metrics file contains unexpected fields: "
            f"{unexpected_text}"
        )

    metric_values = {
        name: payload[name]
        for name in metric_names
    }

    return PerformanceMetrics(**metric_values)


def main() -> int:
    args = build_parser().parse_args()

    try:
        spec = load_test_spec(args.spec)
        metrics = load_metrics_json(args.metrics)
        result = evaluate_metrics(
            metrics,
            spec,
        )

        output_path = write_evaluation_json(
            result,
            args.output,
        )

    except (
        OSError,
        JSONDecodeError,
        TestSpecError,
        TypeError,
        ValueError,
    ) as error:
        print("EVALUATION_INPUT_ERROR")
        print(error)
        return 3

    except EvaluationOutputError as error:
        print("EVALUATION_OUTPUT_ERROR")
        print(error)
        return 4

    print(
        json.dumps(
            result.to_dict(),
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"output={output_path}")

    if result.status is EvaluationStatus.PASS:
        return 0

    if result.status is EvaluationStatus.FAIL:
        return 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())