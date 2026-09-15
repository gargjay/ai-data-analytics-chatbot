"""
tools/column_analyser.py

Analyses a DataFrame and returns the most chart-relevant columns,
automatically excluding ID-like / high-cardinality identifier columns.

Public API
----------
analyse_columns(df)  →  ColumnProfile
    .numeric      – usable numeric cols (IDs removed)
    .categorical  – usable categorical cols (IDs removed)
    .temporal     – date/time cols
    .kpi_cols     – best numeric cols for KPI cards (value metrics first)
    .best_bar     – (cat_col, num_col) best pair for a bar chart
    .best_pie     – cat_col best for a pie chart (low cardinality grouping)
    .best_line    – (x_col, y_col) best pair for a line/trend chart
    .best_scatter – (x_col, y_col) best pair for a scatter plot
    .id_cols      – columns that were detected as identifiers and excluded
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
import numpy as np

# ── Keywords that signal a column is an identifier ──────────────────────────
_ID_PATTERNS = re.compile(
    r"""
    (^|_|\s)                        # word boundary
    (id|ids|no|num|number|code|key  # common id words
    |serial|ref|reference|uuid|guid
    |index|idx|pk|sk|sku|barcode
    |phone|mobile|zip|pincode|pan
    |passport|license|licence|ssn
    |account|acct|invoice|order)
    ($|_|\s|\d)                     # word boundary
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Keywords that strongly suggest a *value* column (good for KPI / numeric use)
_VALUE_KEYWORDS = re.compile(
    r"(sales|revenue|amount|total|profit|loss|cost|price|salary|wage"
    r"|units|qty|quantity|volume|count|score|rate|margin|income|spend"
    r"|budget|forecast|target|actual|balance|payment|earning)",
    re.IGNORECASE,
)

# Keywords that suggest a *grouping* column (good for bar / pie categories)
_GROUP_KEYWORDS = re.compile(
    r"(region|zone|area|territory|country|city|state|location|branch"
    r"|department|dept|division|team|category|type|segment|product"
    r"|channel|platform|gender|status|grade|tier|level|month|quarter"
    r"|year|week|day|period|date|name|label|group)",
    re.IGNORECASE,
)

# Keywords that signal a time/date axis
_TIME_KEYWORDS = re.compile(
    r"(date|month|quarter|year|week|day|period|time|timestamp)",
    re.IGNORECASE,
)


@dataclass
class ColumnProfile:
    numeric:      list[str] = field(default_factory=list)
    categorical:  list[str] = field(default_factory=list)
    temporal:     list[str] = field(default_factory=list)
    kpi_cols:     list[str] = field(default_factory=list)
    best_bar:     Optional[tuple[str, str]] = None   # (cat, num)
    best_pie:     Optional[str] = None               # cat
    best_line:    Optional[tuple[str, str]] = None   # (x, y)
    best_scatter: Optional[tuple[str, str]] = None   # (x, y)
    id_cols:      list[str] = field(default_factory=list)


def _is_id_column(col: str, series: pd.Series) -> bool:
    """Return True if this column looks like a unique identifier."""
    col_lower = col.lower().strip()

    # 1. Name matches an ID pattern
    if _ID_PATTERNS.search(col_lower):
        return True

    # 2. Numeric but every value is unique (or nearly so) and non-negative integers
    if pd.api.types.is_numeric_dtype(series):
        n_unique = series.nunique()
        n_total  = len(series.dropna())
        if n_total == 0:
            return False
        uniqueness = n_unique / n_total
        # If >90 % unique AND all values are whole numbers → likely an ID
        if uniqueness > 0.90 and series.dropna().apply(lambda x: float(x) == int(float(x))).all():
            return True

    # 3. Object column where every value is unique (no meaningful grouping)
    if pd.api.types.is_object_dtype(series):
        n_unique = series.nunique()
        n_total  = len(series.dropna())
        if n_total > 0 and n_unique / n_total > 0.90 and n_total > 20:
            return True

    return False


def _score_numeric(col: str, series: pd.Series) -> int:
    """Higher score = better KPI / aggregation column."""
    score = 0
    if _VALUE_KEYWORDS.search(col):
        score += 10
    if series.min() >= 0:
        score += 2            # non-negative makes more sense to sum
    if series.std() > 0:
        score += 1            # has variance (not a constant)
    return score


def _score_categorical(col: str, series: pd.Series) -> int:
    """Higher score = better grouping column."""
    score = 0
    n_unique = series.nunique()
    if _GROUP_KEYWORDS.search(col):
        score += 10
    # Sweet spot: 2–20 unique values = good grouping column
    if 2 <= n_unique <= 20:
        score += 5
    elif 20 < n_unique <= 50:
        score += 2
    # Penalise very high cardinality (not useful for grouping)
    if n_unique > 100:
        score -= 10
    return score


def _is_temporal(col: str, series: pd.Series) -> bool:
    """Return True if column looks like a date/time axis."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    if _TIME_KEYWORDS.search(col):
        # Try to parse a sample
        try:
            pd.to_datetime(series.dropna().head(5))
            return True
        except Exception:
            pass
    return False


def analyse_columns(df: pd.DataFrame) -> ColumnProfile:
    """
    Main entry point.  Analyses df and returns a ColumnProfile with
    ID columns excluded and the best column selections for each chart type.
    """
    profile = ColumnProfile()

    # ── Step 1: classify every column ───────────────────────────────────
    raw_numeric  = df.select_dtypes(include=["int64", "float64", "int32", "float32"]).columns.tolist()
    raw_object   = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    for col in df.columns:
        series = df[col]

        if _is_id_column(col, series):
            profile.id_cols.append(col)
            continue

        if _is_temporal(col, series):
            profile.temporal.append(col)
        elif col in raw_numeric:
            profile.numeric.append(col)
        elif col in raw_object:
            profile.categorical.append(col)

    # ── Step 2: rank numeric cols by relevance ───────────────────────────
    numeric_scored = sorted(
        profile.numeric,
        key=lambda c: _score_numeric(c, df[c]),
        reverse=True,
    )
    profile.numeric = numeric_scored

    # ── Step 3: rank categorical cols by relevance ───────────────────────
    cat_scored = sorted(
        profile.categorical,
        key=lambda c: _score_categorical(c, df[c]),
        reverse=True,
    )
    profile.categorical = cat_scored

    # ── Step 4: KPI columns (top value metrics, max 4) ───────────────────
    profile.kpi_cols = profile.numeric[:4]

    # ── Step 5: best bar chart pair ──────────────────────────────────────
    if profile.categorical and profile.numeric:
        best_cat = profile.categorical[0]
        best_num = profile.numeric[0]
        # Try to find a more meaningful pair by cross-scoring
        best_score = -999
        for cat in profile.categorical[:5]:        # check top-5 cats
            n_uniq = df[cat].nunique()
            if n_uniq < 2 or n_uniq > 30:
                continue
            for num in profile.numeric[:5]:        # check top-5 numerics
                s = _score_categorical(cat, df[cat]) + _score_numeric(num, df[num])
                if s > best_score:
                    best_score  = s
                    best_cat    = cat
                    best_num    = num
        profile.best_bar = (best_cat, best_num)

    # ── Step 6: best pie chart column ───────────────────────────────────
    for cat in profile.categorical:
        n = df[cat].nunique()
        if 2 <= n <= 8:          # pie charts only work well with few slices
            profile.best_pie = cat
            break
    if profile.best_pie is None and profile.categorical:
        profile.best_pie = profile.categorical[0]

    # ── Step 7: best line chart pair ────────────────────────────────────
    if profile.temporal and profile.numeric:
        profile.best_line = (profile.temporal[0], profile.numeric[0])
    elif profile.categorical and profile.numeric:
        # Use a categorical that looks like a time/period column
        time_cat = next(
            (c for c in profile.categorical if _TIME_KEYWORDS.search(c)), None
        )
        x_col = time_cat or profile.categorical[0]
        profile.best_line = (x_col, profile.numeric[0])

    # ── Step 8: best scatter pair (two distinct numeric cols) ────────────
    if len(profile.numeric) >= 2:
        profile.best_scatter = (profile.numeric[0], profile.numeric[1])

    return profile
