from __future__ import annotations

import argparse

from ai_performance_lab.jtl import (
    JTLCorruptError,
    JTLEmptyError,
    JTLNotFoundError,
    parse_jtl,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse and validate one CSV JMeter JTL file."
    )

    parser.add_argument(
        "jtl_path",
        help="Path to the CSV JTL file.",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        document = parse_jtl(args.jtl_path)

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

    print("JTL_VALID")
    print(f"path={document.source_path}")
    print(f"sample_count={document.sample_count}")

    if document.samples:
        timestamps = [
            sample.timestamp_ms
            for sample in document.samples
        ]

        print(f"first_timestamp_ms={min(timestamps)}")
        print(f"last_timestamp_ms={max(timestamps)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())