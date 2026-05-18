"""I/O utilities for reading and writing CSV/Excel files.

All functions ensure parent directories exist before writing.
Date columns are automatically parsed where applicable.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd


def read_csv(
    path: str | os.PathLike[str],
    parse_dates: bool = True,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read a CSV file and return a DataFrame.

    Parameters
    ----------
    path:
        Path to the CSV file.
    parse_dates:
        If True (default), try to parse ``YYYY-MM-DD`` date columns.
    **kwargs:
        Extra arguments forwarded to ``pandas.read_csv``.

    Returns
    -------
    pd.DataFrame
    """
    if parse_dates:
        kwargs.setdefault("parse_dates", True)
    return pd.read_csv(path, **kwargs)


def write_csv(
    df: pd.DataFrame,
    path: str | os.PathLike[str],
    index: bool = False,
    **kwargs: Any,
) -> None:
    """Write a DataFrame to a CSV file.

    Creates the parent directory if it does not exist.

    Parameters
    ----------
    df:
        DataFrame to write.
    path:
        Destination path.
    index:
        If True, write row indices (default: False).
    **kwargs:
        Extra arguments forwarded to ``DataFrame.to_csv``.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index, **kwargs)


def read_excel(
    path: str | os.PathLike[str],
    sheet_name: str | int | list[str | int] | None = 0,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read an Excel file and return a DataFrame (or dict of DataFrames).

    Parameters
    ----------
    path:
        Path to the Excel file.
    sheet_name:
        Sheet to read.  Defaults to the first sheet (``0``).
        Pass ``None`` to get all sheets as a dict.
    **kwargs:
        Extra arguments forwarded to ``pandas.read_excel``.

    Returns
    -------
    pd.DataFrame | dict[str, pd.DataFrame]
    """
    return pd.read_excel(path, sheet_name=sheet_name, **kwargs)


def write_excel(
    df: pd.DataFrame | dict[str, pd.DataFrame],
    path: str | os.PathLike[str],
    sheet_name: str = "Sheet1",
    index: bool = False,
    **kwargs: Any,
) -> None:
    """Write a DataFrame (or dict of DataFrames) to an Excel file.

    Creates the parent directory if it does not exist.

    Parameters
    ----------
    df:
        DataFrame or dict of {sheet_name: DataFrame} to write.
    path:
        Destination path.
    sheet_name:
        Sheet name (ignored when *df* is a dict).
    index:
        If True, write row indices (default: False).
    **kwargs:
        Extra arguments forwarded to ``DataFrame.to_excel`` or
        ``pd.ExcelWriter``.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    if isinstance(df, dict):
        # Write multiple sheets
        with pd.ExcelWriter(path, engine="openpyxl") as writer:  # type: ignore[call-overload]
            for name, sheet_df in df.items():
                sheet_df.to_excel(writer, sheet_name=name, index=index)
    else:
        df.to_excel(path, sheet_name=sheet_name, index=index, **kwargs)


def list_outputs(pattern: str = "*.csv") -> List[str]:
    """List CSV output files in the standard ``data/outputs/`` directory.

    Returns relative paths (str) sorted by modification time (newest first).
    """
    outputs_dir = Path("data/outputs")
    if not outputs_dir.exists():
        return []
    files = sorted(outputs_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(f) for f in files]
