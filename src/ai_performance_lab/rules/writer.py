from __future__ import annotations

import json
from pathlib import Path

from ai_performance_lab.rules.models import EvaluationResult


class EvaluationOutputError(RuntimeError):
    """评估结果输出失败的异常基类。"""


class EvaluationOutputExistsError(EvaluationOutputError):
    """evaluation.json 已存在时抛出此异常。"""


def write_evaluation_json(
    result: EvaluationResult,
    output_path: str | Path,
) -> Path:
    """写入评估结果文件；若文件已存在，则拒绝覆盖。"""

    resolved_path = Path(output_path).resolve()
    resolved_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "schema_version": "1.0",
        **result.to_dict(),
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
        raise EvaluationOutputExistsError(
            "Evaluation output already exists and "
            f"will not be overwritten: {resolved_path}"
        ) from error

    return resolved_path