from __future__ import annotations

import csv
from pathlib import Path

from ai_performance_lab.jtl.models import (
    JTLDocument,
    JTLSample,
)


REQUIRED_COLUMNS = frozenset(
    {
        "timeStamp",
        "elapsed",
        "label",
        "responseCode",
        "success",
    }
)


class JTLParseError(RuntimeError):
    """Base exception for JTL parsing failures."""


class JTLNotFoundError(JTLParseError):
    """Raised when the requested JTL file does not exist."""


class JTLEmptyError(JTLParseError):
    """Raised when a JTL file contains no CSV header."""


class JTLCorruptError(JTLParseError):
    """Raised when the JTL structure or sample data is invalid."""


def _parse_non_negative_integer(
    value: str | None,
    field_name: str,
    line_number: int,
) -> int:
    if value is None or value.strip() == "":
        raise JTLCorruptError(
            f"Line {line_number}: {field_name} is empty."
        )

    try:
        parsed_value = int(value)
    except ValueError as error:
        raise JTLCorruptError(
            f"Line {line_number}: {field_name} must be an integer, "
            f"got {value!r}."
        ) from error

    if parsed_value < 0:
        raise JTLCorruptError(
            f"Line {line_number}: {field_name} must not be negative, "
            f"got {parsed_value}."
        )

    return parsed_value


def _parse_success(
    value: str | None,
    line_number: int,
) -> bool:
    if value is None:
        raise JTLCorruptError(
            f"Line {line_number}: success is missing."
        )

    normalized_value = value.strip().lower()

    if normalized_value == "true":
        return True

    if normalized_value == "false":
        return False

    raise JTLCorruptError(
        f"Line {line_number}: success must be true or false, "
        f"got {value!r}."
    )


def _validate_header(
    field_names: list[str] | None,
) -> None:
    if field_names is None:
        raise JTLEmptyError(
            "JTL is empty or does not contain a CSV header."
        )

    if len(field_names) != len(set(field_names)):
        raise JTLCorruptError(
            "JTL contains duplicate CSV column names."
        )

    missing_columns = REQUIRED_COLUMNS.difference(field_names)

    if missing_columns:
        missing_text = ", ".join(sorted(missing_columns))
        raise JTLCorruptError(
            f"JTL is missing required columns: {missing_text}"
        )


def parse_jtl(path: str | Path) -> JTLDocument:
    """Parse and validate one CSV JTL file."""

    source_path = Path(path).resolve()

    if not source_path.is_file():
        raise JTLNotFoundError(
            f"JTL file does not exist: {source_path}"
        )

    try:
        with source_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as jtl_file:
            first_non_empty_position: int | None = None

            while True:
                current_position = jtl_file.tell()
                line = jtl_file.readline()

                if line == "":
                    break

                if line.strip():
                    first_non_empty_position = current_position
                    break

            if first_non_empty_position is None:
                raise JTLEmptyError(
                    f"JTL is empty: {source_path}"
                )

            jtl_file.seek(first_non_empty_position)

            reader = csv.DictReader(
                jtl_file,
                strict=True,
            )

            _validate_header(reader.fieldnames)

            samples: list[JTLSample] = []

            for row in reader:
                line_number = reader.line_num

                if None in row:
                    raise JTLCorruptError(
                        f"Line {line_number}: row contains more values "
                        f"than the CSV header."
                    )

                if not any(
                    value is not None and value.strip()
                    for value in row.values()
                ):
                    continue

                label = row.get("label")
                response_code = row.get("responseCode")

                if label is None or label.strip() == "":
                    raise JTLCorruptError(
                        f"Line {line_number}: label is empty."
                    )

                if (
                    response_code is None
                    or response_code.strip() == ""
                ):
                    raise JTLCorruptError(
                        f"Line {line_number}: responseCode is empty."
                    )

                samples.append(
                    JTLSample(
                        timestamp_ms=_parse_non_negative_integer(
                            row.get("timeStamp"),
                            "timeStamp",
                            line_number,
                        ),
                        elapsed_ms=_parse_non_negative_integer(
                            row.get("elapsed"),
                            "elapsed",
                            line_number,
                        ),
                        label=label.strip(),
                        response_code=response_code.strip(),
                        success=_parse_success(
                            row.get("success"),
                            line_number,
                        ),
                    )
                )

    except UnicodeDecodeError as error:
        raise JTLCorruptError(
            f"JTL is not valid UTF-8 text: {source_path}"
        ) from error
    except csv.Error as error:
        raise JTLCorruptError(
            f"JTL contains invalid CSV data near line "
            f"{error}: {source_path}"
        ) from error

    return JTLDocument(
        source_path=source_path,
        samples=tuple(samples),
    )