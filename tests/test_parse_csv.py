"""parse_csv_log must cope with the exports real loggers and spreadsheets produce."""
import io

import numpy as np
import pytest

from core.utils import parse_csv_log

HEADER = "timestamp,temperature_celsius"
ROWS = [("2024-01-01T00:00:00", "5.2"), ("2024-01-01T01:00:00", "5.5"), ("2024-01-01T02:00:00", "6.0")]
EXPECTED = [5.2, 5.5, 6.0]


def make(sep=",", decimal=".", bom=False, newline="\n", header=HEADER):
    lines = [header.replace(",", sep)]
    lines += [f"{t}{sep}{v.replace('.', decimal)}" for t, v in ROWS]
    text = newline.join(lines) + newline
    return ("﻿" + text) if bom else text


def parse_text(text, encoding="utf-8", tmp_path=None, name="log.csv"):
    path = tmp_path / name
    path.write_bytes(text.encode(encoding))
    return parse_csv_log(path)


@pytest.mark.parametrize("kwargs", [
    {},                                   # comma + dot, as before
    {"sep": ";"},                         # semicolon (European / Excel locale)
    {"sep": ";", "decimal": ","},         # semicolon + decimal comma
    {"sep": "\t"},                        # tab-separated
    {"sep": "|"},                         # pipe-separated
    {"bom": True},                        # UTF-8 BOM
    {"sep": ";", "decimal": ",", "bom": True},
    {"newline": "\r\n"},                  # Windows line endings
    {"sep": ";", "decimal": ",", "newline": "\r\n"},
], ids=lambda k: "-".join(f"{a}={b!r}" for a, b in k.items()) or "plain")
def test_file_variants(tmp_path, kwargs):
    ts, tc = parse_text(make(**kwargs), tmp_path=tmp_path)
    assert len(ts) == 3
    assert np.allclose(tc, EXPECTED)
    assert np.all(np.diff(ts) == 3600)


@pytest.mark.parametrize("kwargs", [{}, {"sep": ";", "decimal": ","}, {"bom": True}])
def test_in_memory_input_works(kwargs):
    """The batch API passes io.StringIO; reading the source twice would break it."""
    ts, tc = parse_csv_log(io.StringIO(make(**kwargs)))
    assert np.allclose(tc, EXPECTED)
    ts, tc = parse_csv_log(io.BytesIO(make(**kwargs).encode("utf-8")))
    assert np.allclose(tc, EXPECTED)


def test_windows_cp1252_encoding(tmp_path):
    text = make(header="Time,Température").replace("Time", "timestamp")
    ts, tc = parse_text(text, encoding="cp1252", tmp_path=tmp_path)
    assert np.allclose(tc, EXPECTED)


def test_unix_timestamps_and_decimal_comma(tmp_path):
    text = "ts;temp_c\n1704067200;5,2\n1704070800;5,5\n"
    ts, tc = parse_text(text, tmp_path=tmp_path)
    assert list(ts) == [1704067200.0, 1704070800.0]
    assert np.allclose(tc, [5.2, 5.5])


def test_blank_reading_becomes_nan_not_an_error(tmp_path):
    text = "timestamp;temperature_celsius\n0;4,0\n3600;\n7200;5,0\n"
    ts, tc = parse_text(text, tmp_path=tmp_path)
    assert np.isnan(tc[1]) and tc[0] == 4.0 and tc[2] == 5.0


def test_missing_columns_lists_what_was_found(tmp_path):
    with pytest.raises(ValueError, match=r"Cannot find timestamp column.*Found columns: \['other_col', 'temperature_celsius'\]"):
        parse_text("other_col,temperature_celsius\nfoo,20.5\n", tmp_path=tmp_path)
    with pytest.raises(ValueError, match=r"Cannot find temperature column.*Found columns: \['timestamp', 'other_col'\]"):
        parse_text("timestamp,other_col\n2024-01-01T00:00:00,foo\n", tmp_path=tmp_path)


def test_single_column_file_is_a_clear_error(tmp_path):
    with pytest.raises(ValueError, match="Found columns"):
        parse_text("just_one_column\n1\n2\n", tmp_path=tmp_path)


def test_non_numeric_temperature_names_the_row(tmp_path):
    with pytest.raises(ValueError, match=r"'abc' in row 2"):
        parse_text("timestamp,temperature_celsius\n2024-01-01T00:00:00,5.0\n2024-01-01T01:00:00,abc\n", tmp_path=tmp_path)


def test_empty_file_is_a_value_error(tmp_path):
    with pytest.raises(ValueError):
        parse_text("", tmp_path=tmp_path)
