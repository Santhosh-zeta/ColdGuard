"""Tests for CSV log parsing, including locale variants."""

from pathlib import Path

import numpy as np
import pytest

from core.utils import parse_csv_log

FIXTURES = Path(__file__).parent / "fixtures"


def _write(name: str, content: str) -> Path:
    path = FIXTURES / name
    path.write_text(content, encoding="utf-8")
    return path


def test_normal_comma_dot(tmp_path):
    content = "timestamp,temperature_celsius\n2023-01-01T00:00:00,5.2\n2023-01-01T01:00:00,5.5\n"
    p = tmp_path / "normal.csv"
    p.write_text(content)
    ts, tc = parse_csv_log(p)
    assert len(ts) == 2
    assert np.allclose(tc, [5.2, 5.5])


def test_semicolon_delimiter(tmp_path):
    content = "timestamp;temperature_celsius\n2023-01-01T00:00:00;5.2\n2023-01-01T01:00:00;5.5\n"
    p = tmp_path / "semi.csv"
    p.write_text(content)
    ts, tc = parse_csv_log(p)
    assert len(ts) == 2
    assert np.allclose(tc, [5.2, 5.5])


def test_decimal_comma(tmp_path):
    content = "timestamp;temperature_celsius\n2023-01-01T00:00:00;5,2\n2023-01-01T01:00:00;5,5\n"
    p = tmp_path / "decimal.csv"
    p.write_text(content)
    ts, tc = parse_csv_log(p)
    assert len(ts) == 2
    assert np.allclose(tc, [5.2, 5.5])


def test_utf8_bom(tmp_path):
    content = "\ufefftimestamp,temperature_celsius\n2023-01-01T00:00:00,5.2\n2023-01-01T01:00:00,5.5\n"
    p = tmp_path / "bom.csv"
    p.write_text(content, encoding="utf-8")
    ts, tc = parse_csv_log(p)
    assert len(ts) == 2
    assert np.allclose(tc, [5.2, 5.5])


def test_missing_column_lists_found(tmp_path):
    content = "foo,bar\n2023-01-01T00:00:00,5.2\n"
    p = tmp_path / "bad.csv"
    p.write_text(content)
    with pytest.raises(ValueError, match="Columns found"):
        parse_csv_log(p)
