"""Tests for core.utils.parse_csv_log"""
import pytest
import numpy as np
from pathlib import Path
from core.utils import parse_csv_log


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_normal_csv():
    """Test that normal comma/dot files work as before"""
    timestamps, temps = parse_csv_log(FIXTURES_DIR / "normal.csv")
    
    assert len(timestamps) == 3
    assert len(temps) == 3
    assert temps[0] == pytest.approx(20.5)
    assert temps[1] == pytest.approx(21.0)
    assert temps[2] == pytest.approx(21.5)


def test_semicolon_delimited():
    """Test that semicolon-delimited files are auto-detected"""
    timestamps, temps = parse_csv_log(FIXTURES_DIR / "semicolon.csv")
    
    assert len(timestamps) == 3
    assert len(temps) == 3
    assert temps[0] == pytest.approx(20.5)
    assert temps[1] == pytest.approx(21.0)
    assert temps[2] == pytest.approx(21.5)


def test_decimal_comma():
    """Test that decimal comma format is handled"""
    timestamps, temps = parse_csv_log(FIXTURES_DIR / "decimal_comma.csv")
    
    assert len(timestamps) == 3
    assert len(temps) == 3
    assert temps[0] == pytest.approx(20.5)
    assert temps[1] == pytest.approx(21.0)
    assert temps[2] == pytest.approx(21.5)


def test_bom_prefixed():
    """Test that UTF-8 BOM is handled"""
    timestamps, temps = parse_csv_log(FIXTURES_DIR / "bom.csv")
    
    assert len(timestamps) == 3
    assert len(temps) == 3
    assert temps[0] == pytest.approx(20.5)
    assert temps[1] == pytest.approx(21.0)
    assert temps[2] == pytest.approx(21.5)


def test_missing_timestamp_column():
    """Test that error message includes found columns"""
    # Create a temporary CSV without timestamp column
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("other_col,temperature_celsius\nfoo,20.5\n")
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError) as exc_info:
            parse_csv_log(temp_path)
        
        error_msg = str(exc_info.value)
        assert "Cannot find timestamp column" in error_msg
        assert "Found columns:" in error_msg
        assert "temperature_celsius" in error_msg
    finally:
        temp_path.unlink()


def test_missing_temperature_column():
    """Test that error message includes found columns"""
    # Create a temporary CSV without temperature column
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("timestamp,other_col\n2024-01-01T00:00:00,foo\n")
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError) as exc_info:
            parse_csv_log(temp_path)
        
        error_msg = str(exc_info.value)
        assert "Cannot find temperature column" in error_msg
        assert "Found columns:" in error_msg
        assert "timestamp" in error_msg
    finally:
        temp_path.unlink()
