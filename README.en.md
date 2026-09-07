# AI Performance Lab

[简体中文](README.md) | [English](README.en.md)

An open-source performance engineering platform for evaluating performance against test evidence.

## Project Status

Current version: `0.0.1`

M0 — First Automated Performance Run: completed and validated.

M0 provides a performance testing workflow that operates independently of AI, using defined algorithms to calculate metrics and rules to evaluate results:

```text
Test Spec
→ JMeter
→ Run ID
→ JTL
→ Metrics
→ Rule Engine
→ PASS / FAIL / INVALID
```

The same valid samples and configuration produce the same metrics and evaluation results. Actual load test measurements still vary with the runtime environment. M0 does not include AI test planning or AI result analysis.

## M0 Capabilities

- Validated YAML Test Specs
- A FastAPI demo service with controllable behavior
- A fixed, parameterized JMeter template
- A Python-based JMeter executor
- Unique Run IDs and isolated artifact directories
- CSV JTL parsing and validation
- Deterministic performance metric calculation
- PASS / FAIL / INVALID rule evaluation
- A single command to run the complete automated test suite
- A single command to execute the M0 workflow with JMeter

## Requirements

- Python 3.11 or later
- Java compatible with Apache JMeter 5.6.x
- Apache JMeter 5.6.x
- Windows PowerShell, a Linux shell, or another supported terminal

The initial M0 validation environment used:

- Windows
- Python 3.11.5
- Apache JMeter 5.6.3

## Installation

Create a virtual environment:

```shell
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
& ".\.venv\Scripts\Activate.ps1"
```

Install the project:

```shell
python -m pip install -e .
```

Verify the active interpreter:

```shell
python -c "import sys; print(sys.executable)"
```

## Start the Demo API

```shell
python -m uvicorn examples.demo_api.main:app --host 127.0.0.1 --port 8001
```

M0 provides the following endpoints:

```text
GET /api/normal
GET /api/slow
GET /api/error
```

## Run the Complete M0 Workflow

Example for Windows:

```powershell
python -m ai_performance_lab run --spec "examples\test_specs\normal-e2e.yaml" --jmeter "D:\tools\apache-jmeter-5.6.3\bin\jmeter.bat" --runs-root "runs" --timeout-seconds 30
```

Each execution creates a unique run directory:

```text
runs/
└── RUN-.../
    ├── test-spec.yaml
    ├── test-plan.jmx
    ├── jtl-save.properties
    ├── result.jtl
    ├── jmeter.log
    ├── metrics.json
    ├── evaluation.json
    └── run.json
```

Local run artifacts are excluded from Git version control.

## Evaluation Status

| Status | Meaning |
|---|---|
| PASS | The evidence is valid and all metrics meet the configured thresholds |
| FAIL | The evidence is valid, but at least one metric does not meet its threshold |
| INVALID | The evidence is insufficient or internally inconsistent |

Command exit codes:

| Result | Exit code |
|---|---|
| PASS | 0 |
| FAIL | 1 |
| INVALID | 2 |
| Pipeline error | 10 |

## Run Tests

Run the complete automated test suite:

```shell
python -m pytest
```

The test suite does not require a running Demo API, an actual JMeter process, or network access.

## M0 Validation

See the [M0 validation record (Chinese)](docs/m0-validation.md) for the complete acceptance record.

## Current Scope and Limitations

M0 currently supports:

- A single JMeter execution engine
- HTTP GET demo scenarios
- CSV JTL input
- Local filesystem artifact storage
- Aggregate metrics for each run
- Deterministic threshold rules

M0 does not include:

- AI test planning
- AI result analysis
- Prometheus monitoring
- Report generation
- Jenkins or GitHub Actions integration

## License

Licensed under the [Apache License 2.0](LICENSE).
