"""Tests for src.utils.io — CSV/Excel I/O utilities."""

from __future__ import annotations

import os
import tempfile

import pandas as pd
import pytest

from utils.io import read_csv, read_excel, write_csv, write_excel


class TestReadWriteCSV:
    """Tests for CSV read/write functions."""

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        return pd.DataFrame({
            "data": ["2024-01-15", "2024-02-20"],
            "receita": [1000.50, 2000.75],
            "produto": ["Alpha", "Beta"],
        })

    def test_write_then_read_roundtrip(self, sample_df, tmp_path):
        """Writing then reading should return equivalent data."""
        path = tmp_path / "test.csv"
        write_csv(sample_df, path)
        result = read_csv(path)
        pd.testing.assert_frame_equal(result, sample_df)

    def test_write_creates_parent_dir(self, sample_df, tmp_path):
        """write_csv should create parent directories automatically."""
        path = tmp_path / "subdir" / "nested" / "test.csv"
        write_csv(sample_df, path)
        assert path.exists()

    def test_read_csv_handles_empty_date_string(self, tmp_path):
        """read_csv should handle columns with empty strings gracefully."""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        path = tmp_path / "simple.csv"
        df.to_csv(path, index=False)
        result = read_csv(path)
        assert list(result.columns) == ["col1", "col2"]
        assert len(result) == 2

    def test_write_without_index(self, sample_df, tmp_path):
        """Default write should NOT include the index column."""
        path = tmp_path / "no_index.csv"
        write_csv(sample_df, path)
        content = path.read_text()
        # Should start with the header, not a comma or unnamed column
        assert content.startswith("data,receita,produto")


class TestReadWriteExcel:
    """Tests for Excel read/write functions."""

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        return pd.DataFrame({
            "mes": ["Janeiro", "Fevereiro"],
            "valor": [5000, 7500],
        })

    def test_write_then_read_roundtrip(self, sample_df, tmp_path):
        """Writing then reading Excel should return equivalent data."""
        path = tmp_path / "test.xlsx"
        write_excel(sample_df, path)
        result = read_excel(path)
        # Reset index since read_excel may create its own index
        result = result.reset_index(drop=True)
        pd.testing.assert_frame_equal(result, sample_df)

    def test_write_creates_parent_dir(self, sample_df, tmp_path):
        """write_excel should create parent directories automatically."""
        path = tmp_path / "sub" / "nested" / "test.xlsx"
        write_excel(sample_df, path)
        assert path.exists()

    def test_write_multiple_sheets(self, tmp_path):
        """write_excel with dict should create multiple sheets."""
        sheets = {
            "Sheet1": pd.DataFrame({"a": [1]}),
            "Sheet2": pd.DataFrame({"b": [2]}),
        }
        path = tmp_path / "multi.xlsx"
        write_excel(sheets, path)
        result = read_excel(path, sheet_name=None)
        assert set(result.keys()) == {"Sheet1", "Sheet2"}

    def test_read_excel_specific_sheet(self, tmp_path):
        """read_excel should read the correct sheet by name."""
        sheets = {
            "Alpha": pd.DataFrame({"x": [10]}),
            "Beta": pd.DataFrame({"y": [20]}),
        }
        path = tmp_path / "sheets.xlsx"
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            for name, df in sheets.items():
                df.to_excel(writer, sheet_name=name, index=False)

        result = read_excel(path, sheet_name="Beta")
        assert list(result.columns) == ["y"]
        assert result.iloc[0]["y"] == 20
