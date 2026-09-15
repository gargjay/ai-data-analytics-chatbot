"""
tools/powerbi_table_tool.py
Power BI-style summary table drawn entirely with matplotlib patches + text
(no ax.table() widget which can cause rendering issues in Streamlit).

Colour palette mirrors the official Power BI brand:
  Primary yellow  #F2C811   (Power BI logo accent)
  Dark header     #1B1A19   (Power BI dark chrome)
  Mid header      #252423   (Power BI panel background)
  Row even        #FFF8DC   (warm cream, matching PBI canvas)
  Row odd         #FFFFFF

For every column in the dataset it shows:
  Numeric  → Total (Sum), Average, Median, Min, Max, Std Dev, Count, Nulls
  Category → Count, Unique, Most Frequent, Frequency, Nulls
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── Power BI Brand Palette ──────────────────────────────────────────────────
NAVY      = "#1B1A19"   # Power BI dark chrome / header
BLUE_MID  = "#252423"   # Power BI panel background (numeric section banner)
GREEN_HDR = "#217346"   # Power BI green accent  (categorical section banner)
ACCENT    = "#F2C811"   # Power BI signature yellow — used for borders & title
ROW_EVEN  = "#FFF8DC"   # warm cream canvas
ROW_ODD   = "#FFFFFF"
WHITE     = "#FFFFFF"
DARK_TXT  = "#1B1A19"
GRAY      = "#605E5C"   # Power BI neutral grey
BORDER    = "#F2C811"   # yellow border — gives the unmistakable PBI look


def _fmt(val):
    """Format a cell value for display."""
    if val is None:
        return "—"
    try:
        if pd.isna(val):
            return "—"
    except Exception:
        pass
    if isinstance(val, float):
        return f"{val:,.2f}"
    if isinstance(val, int):
        return f"{val:,}"
    return str(val)


def _draw_section(ax, headers, rows, y_top, row_h, section_label, hdr_color):
    """
    Draw one section (numeric or categorical) on `ax` using patches + text.
    Returns the y position after the last row.
    """
    n_cols = len(headers)
    col_w  = 1.0 / n_cols

    # ── Section banner ────────────────────────────────────────────────────
    ax.add_patch(mpatches.FancyBboxPatch(
        (0, y_top - row_h), 1, row_h,
        boxstyle="square,pad=0", linewidth=0,
        facecolor=hdr_color, transform=ax.transAxes, zorder=2, clip_on=False))
    # Power BI style: yellow left accent bar on section banners
    ax.add_patch(mpatches.FancyBboxPatch(
        (0, y_top - row_h), 0.006, row_h,
        boxstyle="square,pad=0", linewidth=0,
        facecolor=ACCENT, transform=ax.transAxes, zorder=3, clip_on=False))
    ax.text(0.018, y_top - row_h / 2, section_label,
            transform=ax.transAxes, color=WHITE,
            fontsize=11, fontweight="bold", va="center", zorder=4)
    y_top -= row_h

    # ── Column header row ─────────────────────────────────────────────────
    for ci, hdr in enumerate(headers):
        ax.add_patch(mpatches.FancyBboxPatch(
            (ci * col_w, y_top - row_h), col_w, row_h,
            boxstyle="square,pad=0", linewidth=0.5,
            edgecolor=WHITE, facecolor=NAVY,
            transform=ax.transAxes, zorder=2, clip_on=False))
        ax.text((ci + 0.5) * col_w, y_top - row_h / 2, hdr,
                transform=ax.transAxes, color=WHITE,
                fontsize=9, fontweight="bold",
                va="center", ha="center", zorder=3)
    y_top -= row_h

    # ── Data rows ─────────────────────────────────────────────────────────
    for ri, row in enumerate(rows):
        bg = ROW_EVEN if ri % 2 == 0 else ROW_ODD
        for ci, cell_val in enumerate(row):
            ax.add_patch(mpatches.FancyBboxPatch(
                (ci * col_w, y_top - row_h), col_w, row_h,
                boxstyle="square,pad=0", linewidth=0.4,
                edgecolor=BORDER, facecolor=bg,
                transform=ax.transAxes, zorder=2, clip_on=False))
            ax.text((ci + 0.5) * col_w, y_top - row_h / 2, str(cell_val),
                    transform=ax.transAxes, color=DARK_TXT,
                    fontsize=8.5, va="center", ha="center", zorder=3)
        y_top -= row_h

    # Gap between sections
    return y_top - 0.03


def create_data_table(title=None):
    """
    Build and return a Power BI-style summary matplotlib figure covering
    ALL columns in the loaded dataset.
    Returns {"type": "chart", "figure": fig, "message": str} on success,
    or an error string on failure.
    """
    if st.session_state.data is None:
        return "No data loaded. Please upload a file first."

    df = st.session_state.data

    try:
        numeric_cols     = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=["object", "category", "bool"]).columns.tolist()

        # ── Build numeric rows ────────────────────────────────────────────
        num_headers = ["Column", "Total (Sum)", "Average", "Median",
                       "Min", "Max", "Std Dev", "Count", "Nulls"]
        num_rows = []
        for col in numeric_cols:
            s = df[col]
            num_rows.append([
                col,
                _fmt(s.sum()),
                _fmt(s.mean()),
                _fmt(s.median()),
                _fmt(s.min()),
                _fmt(s.max()),
                _fmt(s.std()),
                _fmt(int(s.count())),
                _fmt(int(s.isna().sum())),
            ])

        # ── Build categorical rows ────────────────────────────────────────
        cat_headers = ["Column", "Count", "Unique Values",
                       "Most Frequent", "Frequency", "Nulls"]
        cat_rows = []
        for col in categorical_cols:
            s = df[col]
            vc = s.value_counts()
            top_val  = str(vc.index[0])[:28] if len(vc) > 0 else "—"
            top_freq = int(vc.iloc[0]) if len(vc) > 0 else 0
            cat_rows.append([
                col,
                _fmt(int(s.count())),
                _fmt(int(s.nunique())),
                top_val,
                _fmt(top_freq),
                _fmt(int(s.isna().sum())),
            ])

        if not num_rows and not cat_rows:
            return "No columns found to summarise."

        ROW_H    = 0.052
        sections = 0
        total_r  = 0
        if num_rows:
            total_r  += len(num_rows) + 2
            sections += 1
        if cat_rows:
            total_r  += len(cat_rows) + 2
            sections += 1
        gap_space = sections * 0.03

        fig_h = max(5, total_r * 0.38 + gap_space * 10 + 1.5)
        fig_w = 20

        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        fig.patch.set_facecolor("#FAF9F8")   # Power BI canvas background
        ax.set_facecolor("#FAF9F8")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        # ── Power BI style title bar ──────────────────────────────────────
        # Yellow accent strip at top-left (mimics PBI report header)
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.0, 0.955), 0.007, 0.04,
            boxstyle="square,pad=0", linewidth=0,
            facecolor=ACCENT, transform=ax.transAxes, zorder=3, clip_on=False))
        ax.text(0.015, 0.975,
                title or "⚡ Power BI Summary Table — Full Column Analysis",
                transform=ax.transAxes, color=NAVY,
                fontsize=15, fontweight="bold", va="center")

        y = 0.93   # start just below title

        if num_rows:
            y = _draw_section(ax, num_headers, num_rows, y, ROW_H,
                              "🔢  NUMERIC COLUMNS", BLUE_MID)
        if cat_rows:
            y = _draw_section(ax, cat_headers, cat_rows, y, ROW_H,
                              "🔤  CATEGORICAL COLUMNS", GREEN_HDR)

        # ── Footer ───────────────────────────────────────────────────────
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.0, 0.0), 1.0, 0.025,
            boxstyle="square,pad=0", linewidth=0,
            facecolor=NAVY, transform=ax.transAxes, zorder=2, clip_on=False))
        ax.text(0.01, 0.012,
                (f"Rows: {len(df):,}  |  Total columns: {len(df.columns)}"
                 f"  |  Numeric: {len(numeric_cols)}"
                 f"  |  Categorical: {len(categorical_cols)}"
                 f"  |  {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}  "
                 f"|  Powered by Power BI Style"),
                transform=ax.transAxes, color=ACCENT,
                fontsize=8, style="italic", va="center")

        plt.tight_layout()

        return {
            "type": "chart",
            "figure": fig,
            "message": (
                f"Power BI summary table created — "
                f"{len(numeric_cols)} numeric columns (9 stats each), "
                f"{len(categorical_cols)} categorical columns (5 stats each)."
            ),
        }

    except Exception as e:
        return f"Error creating Power BI table: {e}"
