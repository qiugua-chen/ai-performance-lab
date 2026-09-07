from __future__ import annotations

import argparse
import json

from ai_performance_lab.jtl import (
    JTLCorruptError,
    JTLEmptyError,
    JTLNotFoundError,
    parse_jtl,
)
from ai_performance_lab.metrics import (
    MetricsCalculationError,
    MetricsEmptyError,
    MetricsOutputError,
    calculate_metrics,
    write_metrics_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="根据一个 CSV 格式的 JTL 文件计算性能指标。"
    )

    parser.add_argument(
        "jtl_path",
        help="已校验的 CSV 格式 JTL 文件路径。",
    )
    parser.add_argument(
        "--output",
        help="可选的 metrics.json 输出路径，目标文件必须尚不存在。",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        document = parse_jtl(args.jtl_path)
        metrics = calculate_metrics(document.samples)

        if args.output:
            output_path = write_metrics_json(
                metrics,
                args.output,
            )
        else:
            output_path = None

    except JTLEmptyError as error:
        print("JTL_EMPTY")
        print(error)
        return 2

    except JTLCorruptError as error:
        print("JTL_CORRUPT")
        print(error)
        return 3

    except JTLNotFoundError as error:
        print("JTL_NOT_FOUND")
        print(error)
        return 4

    except MetricsEmptyError as error:
        print("METRICS_EMPTY")
        print(error)
        return 5

    except MetricsCalculationError as error:
        print("METRICS_INVALID")
        print(error)
        return 6

    except MetricsOutputError as error:
        print("METRICS_OUTPUT_ERROR")
        print(error)
        return 7

    print("METRICS_VALID")
    print(
        json.dumps(
            metrics.to_dict(),
            ensure_ascii=False,
            indent=2,
        )
    )

    if output_path is not None:
        print(f"output={output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())