from __future__ import annotations

import json
from pathlib import Path

from ai_performance_lab.metrics.models import PerformanceMetrics


class MetricsOutputError(RuntimeError):
    """指标输出失败的异常基类。"""


class MetricsOutputExistsError(MetricsOutputError):
    """metrics.json 已存在时抛出此异常。"""


def write_metrics_json(
    metrics: PerformanceMetrics,
    output_path: str | Path,
) -> Path:
    """写入指标，且不覆盖已有产物。"""

    resolved_path = Path(output_path).resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": "1.0",
        **metrics.to_dict(),
    }

    try:
        with resolved_path.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as output_file:
            json.dump(
                payload,
                output_file,
                ensure_ascii=False,
                indent=2,
            )
            output_file.write("\n")
    except FileExistsError as error:
        raise MetricsOutputExistsError(
            f"Metrics output already exists and will not be overwritten: "
            f"{resolved_path}"
        ) from error

    return resolved_path