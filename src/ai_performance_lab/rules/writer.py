from __future__ import annotations

import json
from pathlib import Path

from ai_performance_lab.rules.models import EvaluationResult


class EvaluationOutputError(RuntimeError):
    """Base exception for evaluation output failures."""


class EvaluationOutputExistsError(EvaluationOutputError):
    """Raised when evaluation.json already exists."""


def write_evaluation_json(
    result: EvaluationResult,
    output_path: str | Path,
) -> Path:
    """Write an immutable evaluation artifact."""

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