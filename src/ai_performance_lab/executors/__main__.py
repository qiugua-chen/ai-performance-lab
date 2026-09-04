from __future__ import annotations

import argparse

from ai_performance_lab.executors import (
    JMeterCommandNotFoundError,
    JMeterExecutionError,
    JMeterProcessError,
    JMeterTimeoutError,
    execute_jmeter,
)
from ai_performance_lab.test_spec.loader import (
    TestSpecError,
    load_test_spec,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute the deterministic M0 JMeter template."
    )

    parser.add_argument(
        "--spec",
        required=True,
        help="Path to the Test Spec YAML file.",
    )
    parser.add_argument(
        "--jmeter",
        required=True,
        help="Path to jmeter.bat, jmeter, or a command available on PATH.",
    )
    parser.add_argument(
        "--template",
        default="jmeter/templates/http_get.jmx",
        help="Path to the deterministic JMeter template.",
    )
    parser.add_argument(
        "--result-properties",
        default="jmeter/config/jtl-save.properties",
        help="Path to the fixed JTL save properties.",
    )
    parser.add_argument(
        "--jtl",
        required=True,
        help="New path for the JTL result file.",
    )
    parser.add_argument(
        "--log",
        required=True,
        help="New path for the JMeter execution log.",
    )
    parser.add_argument(
        "--timeout-seconds",
        required=True,
        type=float,
        help="Maximum JMeter process execution time.",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        spec = load_test_spec(args.spec)

        result = execute_jmeter(
            spec=spec,
            jmeter_command=args.jmeter,
            template_path=args.template,
            result_properties_path=args.result_properties,
            jtl_path=args.jtl,
            log_path=args.log,
            timeout_seconds=args.timeout_seconds,
        )

    except TestSpecError as error:
        print("INVALID_SPEC")
        print(error)
        return 2

    except JMeterCommandNotFoundError as error:
        print("COMMAND_NOT_FOUND")
        print(error)
        return 3

    except JMeterTimeoutError as error:
        print("TIMEOUT")
        print(error)
        return 4

    except JMeterProcessError as error:
        print("EXECUTION_FAILED")
        print(f"exit_code={error.exit_code}")

        if error.stdout:
            print("stdout:")
            print(error.stdout)

        if error.stderr:
            print("stderr:")
            print(error.stderr)

        return 5

    except JMeterExecutionError as error:
        print("EXECUTION_ERROR")
        print(error)
        return 6

    print("SUCCESS")
    print(f"exit_code={result.exit_code}")
    print(f"elapsed_seconds={result.elapsed_seconds:.3f}")
    print(f"jtl={result.jtl_path}")
    print(f"log={result.log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())