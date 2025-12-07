"""
Utility helpers for loading spreadsheet and Word documents inside example workspaces.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import openpyxl
import pandas as pd
from docx import Document


def _strip_lines(lines: Iterable[str]) -> list[str]:
    return [line.strip() for line in lines if line and line.strip()]


def load_clean_excel(path: str | Path, sheet: str | int | None = None) -> pd.DataFrame:
    """
    Load an Excel sheet into a cleaned pandas DataFrame.

    Cleaning steps:
    - drop fully empty rows
    - assume the first remaining row is the header
    - drop rows whose first column starts with '#'
    - attempt numeric casting for columns with '数量' or '数值' in the name
    """
    file_path = Path(path)
    wb = openpyxl.load_workbook(file_path, data_only=True)
    if sheet is None:
        ws = wb.active
    elif isinstance(sheet, int):
        ws = wb.worksheets[sheet]
    else:
        ws = wb[sheet]

    rows: list[list[object]] = []
    for row in ws.iter_rows(values_only=True):
        rows.append(list(row))

    rows = [r for r in rows if any(c is not None and str(c).strip() != "" for c in r)]
    if not rows:
        return pd.DataFrame()

    header, *data_rows = rows
    df = pd.DataFrame(data_rows, columns=header)

    first_col = df.columns[0]
    df = df[~df[first_col].astype(str).str.startswith("#")]

    numeric_cols = [c for c in df.columns if "数量" in str(c) or "数值" in str(c)]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def load_docx_text(path: str | Path) -> str:
    """Extract plain text from a .docx file."""
    file_path = Path(path)
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(_strip_lines(paragraphs))


def load_word_text(path: str | Path) -> str:
    """
    Extract text from Word files (.docx or .doc).

    For .docx this uses python-docx directly.
    For legacy .doc files, pypandoc is attempted if available; otherwise an error
    is raised with a hint to convert to .docx first.
    """
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".docx":
        return load_docx_text(file_path)
    if suffix == ".doc":
        try:
            import pypandoc  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                ".doc support requires pypandoc and pandoc installed; "
                "convert the file to .docx or install pypandoc."
            ) from exc
        return pypandoc.convert_file(str(file_path), "plain")  # type: ignore
    raise ValueError(f"Unsupported Word file suffix: {suffix}")


__all__ = [
    "load_clean_excel",
    "load_docx_text",
    "load_word_text",
]
