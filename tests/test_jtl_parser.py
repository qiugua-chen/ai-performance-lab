from __future__ import annotations

from pathlib import Path

import pytest

from ai_performance_lab.jtl import (
    JTLCorruptError,
    JTLEmptyError,
    parse_jtl,
)


VALID_HEADER = (
    "timeStamp,elapsed,label,responseCode,"
    "responseMessage,success\n"
)


def test_parse_normal_jtl(
    tmp_path: Path,
) -> None:
    jtl_path = tmp_path / "normal.jtl"

    jtl_path.write_text(
        VALID_HEADER
        + "1725440000000,120,HTTP GET,200,OK,true\n"
        + "1725440000200,350,HTTP GET,500,Error,false\n",
        encoding="utf-8",
    )

    document = parse_jtl(jtl_path)

    assert document.sample_count == 2

    first_sample = document.samples[0]
    second_sample = document.samples[1]

    assert first_sample.timestamp_ms == 1725440000000
    assert first_sample.elapsed_ms == 120
    assert first_sample.response_code == "200"
    assert first_sample.success is True

    assert second_sample.elapsed_ms == 350
    assert second_sample.response_code == "500"
    assert second_sample.success is False


def test_parse_empty_jtl_is_rejected(
    tmp_path: Path,
) -> None:
    jtl_path = tmp_path / "empty.jtl"
    jtl_path.write_text("", encoding="utf-8")

    with pytest.raises(JTLEmptyError):
        parse_jtl(jtl_path)


def test_parse_whitespace_only_jtl_is_rejected(
    tmp_path: Path,
) -> None:
    jtl_path = tmp_path / "whitespace.jtl"
    jtl_path.write_text(
        "\n   \n\t\n",
        encoding="utf-8",
    )

    with pytest.raises(JTLEmptyError):
        parse_jtl(jtl_path)


def test_parse_header_only_jtl_returns_zero_samples(
    tmp_path: Path,
) -> None:
    jtl_path = tmp_path / "header-only.jtl"
    jtl_path.write_text(
        VALID_HEADER,
        encoding="utf-8",
    )

    document = parse_jtl(jtl_path)

    assert document.sample_count == 0
    assert document.samples == ()


def test_parse_corrupt_jtl_is_rejected(
    tmp_path: Path,
) -> None:
    jtl_path = tmp_path / "corrupt.jtl"

    jtl_path.write_text(
        VALID_HEADER
        + "1725440000000,not-a-number,HTTP GET,200,OK,true\n",
        encoding="utf-8",
    )

    with pytest.raises(
        JTLCorruptError,
        match="elapsed must be an integer",
    ):
        parse_jtl(jtl_path)


def test_parse_jtl_with_missing_columns_is_rejected(
    tmp_path: Path,
) -> None:
    jtl_path = tmp_path / "missing-columns.jtl"

    jtl_path.write_text(
        "timeStamp,elapsed,label\n"
        "1725440000000,120,HTTP GET\n",
        encoding="utf-8",
    )

    with pytest.raises(
        JTLCorruptError,
        match="missing required columns",
    ):
        parse_jtl(jtl_path)