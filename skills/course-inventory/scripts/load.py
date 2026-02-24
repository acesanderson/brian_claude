#!/usr/bin/env python3
"""Load LinkedIn Learning course inventory with parquet caching.

Usage:
    import sys
    sys.path.insert(0, '/Users/bianders/.claude/skills/course-inventory')
    from scripts.load import load_data, load_en
    df = load_en()  # active en_US courses
    df = load_data()  # all rows, all locales
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

XLSX_PATH = Path("/Users/bianders/.claude/skills/courselist_all (1).xlsx")
CACHE_PATH = Path("/Users/bianders/.claude/skills/course-inventory/.cache/catalog.parquet")


def load_data() -> pd.DataFrame:
    """Load full catalog (all locales, all statuses). Uses parquet cache when fresh."""
    if CACHE_PATH.exists() and CACHE_PATH.stat().st_mtime >= XLSX_PATH.stat().st_mtime:
        return pd.read_parquet(CACHE_PATH)
    df = pd.read_excel(XLSX_PATH)
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CACHE_PATH, index=False)
    return df


def load_en(active_only: bool = True) -> pd.DataFrame:
    """Load en_US courses. active_only=True filters to Activation Status == ACTIVE."""
    df = load_data()
    df = df[df["Locale"] == "en_US"].copy()
    if active_only:
        df = df[df["Activation Status"] == "ACTIVE"]
    return df


def hours(df: pd.DataFrame, col: str = "Visible Duration") -> pd.Series:
    """Convert a duration column (seconds) to hours."""
    return (df[col] / 3600).round(2)


def skills_explode(df: pd.DataFrame, col: str = "Skills EN") -> pd.DataFrame:
    """Explode the comma-separated skills column into one row per skill."""
    return (
        df.dropna(subset=[col])
        .assign(**{col: df[col].str.split(r",\s*")})
        .explode(col)
        .assign(**{col: lambda x: x[col].str.strip()})
    )


if __name__ == "__main__":
    df = load_data()
    en = df[df["Locale"] == "en_US"]
    active = en[en["Activation Status"] == "ACTIVE"]
    print(f"Total rows:     {len(df):>7,}")
    print(f"en_US rows:     {len(en):>7,}")
    print(f"en_US active:   {len(active):>7,}")
    print(f"Columns:        {len(df.columns)}")
