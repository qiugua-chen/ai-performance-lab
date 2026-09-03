import sys
from pathlib import Path

from ai_performance_lab.test_spec import (
    TestSpecError,
    load_test_spec,
)


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "Usage: python -m ai_performance_lab.test_spec <spec.yaml>",
            file=sys.stderr,
        )
        return 2

    spec_path = Path(sys.argv[1])

    try:
        test_spec = load_test_spec(spec_path)
    except TestSpecError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1

    print(f"VALID: {spec_path}")
    print(test_spec.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())