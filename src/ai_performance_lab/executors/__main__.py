from __future__ import annotations

import argparse

from ai_performance_lab.executors import (
    JMeterCommandNotFoundError,
    JMeterExecutionError,
    JMeterProcessError,
    JMeterTimeoutError,
    execute_jmeter,
)
from ai_performance_lab.runs import (
    RunArtifactError,
    create_run_artifacts,
    stage_run_inputs,
    write_run_manifest,
)
from ai_performance_lab.test_spec.loader import (
    TestSpecError,
    load_test_spec,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute JMeter inside an isolated M0 Run directory."
    )

    parser.add_argument(
        "--spec",
        required=True,
        help="Path to the Test Spec YAML file.",
    )
    parser.add_argument(
        "--jmeter",
        required=True,
        help="Path to jmeter.bat, jmeter, or a command on PATH.",
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
        "--runs-root",
        default="runs",
        help="Root directory used to store isolated Runs.",
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
        artifacts = create_run_artifacts(args.runs_root)
    except (RunArtifactError, ValueError, OSError) as error:
        print("RUN_CREATION_ERROR")
        print(error)
        return 7

    print(f"run_id={artifacts.run_id}")
    print(f"run_directory={artifacts.directory}")

    try:
        stage_run_inputs(
            artifacts=artifacts,
            test_spec_source=args.spec,
            test_plan_source=args.template,
            result_properties_source=args.result_properties,
        )

        spec = load_test_spec(artifacts.test_spec_path)

        result = execute_jmeter(
            spec=spec,
            jmeter_command=args.jmeter,
            template_path=artifacts.test_plan_path,
            result_properties_path=artifacts.result_properties_path,
            jtl_path=artifacts.jtl_path,
            log_path=artifacts.jmeter_log_path,
            timeout_seconds=args.timeout_seconds,
        )

    except TestSpecError as error:
        write_run_manifest(
            artifacts,
            status="INVALID_SPEC",
            details={"error": str(error), "exit_code": 2},
        )
        print("INVALID_SPEC")
        print(error)
        return 2

    except JMeterCommandNotFoundError as error:
        write_run_manifest(
            artifacts,
            status="COMMAND_NOT_FOUND",
            details={"error": str(error), "exit_code": 3},
        )
        print("COMMAND_NOT_FOUND")
        print(error)
        return 3

    except JMeterTimeoutError as error:
        write_run_manifest(
            artifacts,
            status="TIMEOUT",
            details={"error": str(error), "exit_code": 4},
        )
        print("TIMEOUT")
        print(error)
        return 4

    except JMeterProcessError as error:
        write_run_manifest(
            artifacts,
            status="EXECUTION_FAILED",
            details={
                "error": str(error),
                "exit_code": error.exit_code,
            },
        )
        print("EXECUTION_FAILED")
        print(f"exit_code={error.exit_code}")

        if error.stdout:
            print("stdout:")
            print(error.stdout)

        if error.stderr:
            print("stderr:")
            print(error.stderr)

        return 5

    except (JMeterExecutionError, RunArtifactError) as error:
        write_run_manifest(
            artifacts,
            status="EXECUTION_ERROR",
            details={"error": str(error), "exit_code": 6},
        )
        print("EXECUTION_ERROR")
        print(error)
        return 6

    write_run_manifest(
        artifacts,
        status="SUCCESS",
        details={
            "exit_code": result.exit_code,
            "elapsed_seconds": round(result.elapsed_seconds, 3),
        },
    )

    print("SUCCESS")
    print(f"exit_code={result.exit_code}")
    print(f"elapsed_seconds={result.elapsed_seconds:.3f}")
    print(f"jtl={result.jtl_path}")
    print(f"log={result.log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())