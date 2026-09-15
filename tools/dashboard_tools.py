"""
tools/dashboard_tools.py
Dashboard configuration and rendering tools.
Uses column_analyser to automatically pick the most relevant columns
and exclude ID / high-cardinality identifier columns.
"""
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import pandas as pd

from tools.table_tool import create_data_table
from tools.column_analyser import analyse_columns

COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#96CEB4", "#F7DC6F", "#BB8FCE"]

DEFAULT_CONFIG = {
    "include_kpis":       True,
    "include_bar_chart":  True,
    "include_pie_chart":  True,
    "include_line_chart": True,
    "include_scatter":    False,
    "include_table":      False,
    "bar_chart_columns":  None,
    "pie_chart_column":   None,
    "line_chart_columns": None,
    "scatter_columns":    None,
}


def _get_config():
    if "dashboard_config" not in st.session_state:
        st.session_state.dashboard_config = DEFAULT_CONFIG.copy()
    return st.session_state.dashboard_config


def configure_dashboard(
    include_kpis=None, include_bar=None, include_pie=None,
    include_line=None, include_scatter=None, include_table=None,
    bar_columns=None, pie_column=None, line_columns=None, scatter_columns=None,
):
    config = _get_config()
    toggles = {
        "include_kpis":       include_kpis,
        "include_bar_chart":  include_bar,
        "include_pie_chart":  include_pie,
        "include_line_chart": include_line,
        "include_scatter":    include_scatter,
        "include_table":      include_table,
    }
    for key, val in toggles.items():
        if val is not None:
            config[key] = val
    if bar_columns:     config["bar_chart_columns"]  = bar_columns
    if pie_column:      config["pie_chart_column"]   = pie_column
    if line_columns:    config["line_chart_columns"] = line_columns
    if scatter_columns: config["scatter_columns"]    = scatter_columns
    st.session_state.dashboard_config = config
    parts = []
    if config["include_kpis"]:       parts.append("KPI cards")
    if config["include_bar_chart"]:  parts.append("bar chart")
    if config["include_pie_chart"]:  parts.append("pie chart")
    if config["include_line_chart"]: parts.append("line chart")
    if config["include_scatter"]:    parts.append("scatter plot")
    if config["include_table"]:      parts.append("tableau summary table")
    return f"Dashboard configured to include: {', '.join(parts) or 'nothing'}"


def show_dashboard_config():
    config = _get_config()
    def _s(f): return "✅ Included" if f else "❌ Excluded"
    lines = ["📊 Current Dashboard Configuration:\n"]
    lines.append(f"• KPI Cards:      {_s(config['include_kpis'])}")
    bar_info = ""
    if config["bar_chart_columns"]:
        bc = config["bar_chart_columns"]
        bar_info = f" ({bc.get('value','value')} by {bc.get('category','category')})"
    lines.append(f"• Bar Chart:      {_s(config['include_bar_chart'])}{bar_info}")
    pie_info = f" ({config['pie_chart_column']})" if config["pie_chart_column"] else ""
    lines.append(f"• Pie Chart:      {_s(config['include_pie_chart'])}{pie_info}")
    lines.append(f"• Line Chart:     {_s(config['include_line_chart'])}")
    lines.append(f"• Scatter Plot:   {_s(config['include_scatter'])}")
    lines.append(f"• Tableau Table:  {_s(config.get('include_table', False))}")
    return "\n".join(lines)


def reset_dashboard_config():
    st.session_state.dashboard_config = DEFAULT_CONFIG.copy()
    return "Dashboard reset to defaults (KPIs, bar chart, pie chart, line chart)."


def create_custom_dashboard():
    """
    Smart dashboard: auto-excludes ID/identifier columns and picks the most
    relevant column combinations for each chart type.
    Manual overrides in dashboard_config always take precedence.
    """
    if st.session_state.data is None:
        return "No data loaded."

    df     = st.session_state.data
    config = _get_config()
    profile = analyse_columns(df)

    if not profile.numeric and not profile.categorical:
        return (
            "No usable columns found after excluding identifier columns. "
            f"Excluded: {profile.id_cols}"
        )

    chart_flags = [config["include_kpis"], config["include_bar_chart"],
                   config["include_pie_chart"], config["include_line_chart"],
                   config["include_scatter"]]
    if sum(chart_flags) == 0 and not config.get("include_table"):
        return "No components selected. Use 'configure dashboard' to add some."

    try:
        fig = plt.figure(figsize=(20, 13))
        excl_note = ""
        if profile.id_cols:
            excl_note = f"  |  auto-excluded: {', '.join(profile.id_cols[:4])}"
        fig.suptitle(f"📊 SMART DASHBOARD{excl_note}",
                     fontsize=17, fontweight="bold", y=0.99)

        if config["include_kpis"]:
            gs      = GridSpec(3, 3, figure=fig, hspace=0.55, wspace=0.45)
            cur_row = 1
        else:
            gs      = GridSpec(2, 3, figure=fig, hspace=0.55, wspace=0.45)
            cur_row = 0

        comp_count = 0

        # ── KPI Cards ────────────────────────────────────────────────────
        if config["include_kpis"] and profile.kpi_cols:
            for i, col in enumerate(profile.kpi_cols[:3]):
                ax    = fig.add_subplot(gs[0, i])
                total = df[col].sum()
                avg   = df[col].mean()
                money = any(k in col.lower() for k in
                            ["sales","revenue","price","amount","cost",
                             "profit","income","payment","salary","wage"])
                prefix  = "$" if money else ""
                val_txt = f"{prefix}{total:,.0f}" if total >= 1000 else f"{prefix}{total:.2f}"
                ax.text(0.5, 0.68, val_txt,
                        ha="center", va="center", fontsize=22, fontweight="bold", color="#1A1F5E")
                ax.text(0.5, 0.44, f"Total {col}",
                        ha="center", va="center", fontsize=11, fontweight="bold")
                ax.text(0.5, 0.24, f"Avg: {avg:,.2f}",
                        ha="center", va="center", fontsize=10, color="gray")
                ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
                ax.add_patch(mpatches.Rectangle((0.03, 0.03), 0.94, 0.94,
                             fill=False, edgecolor="#4ECDC4", linewidth=3))
            comp_count += 1

        # ── Bar Chart ────────────────────────────────────────────────────
        if config["include_bar_chart"]:
            if config["bar_chart_columns"]:
                cat_col = config["bar_chart_columns"].get("category")
                num_col = config["bar_chart_columns"].get("value")
                if (cat_col not in df.columns or num_col not in df.columns
                        or cat_col in profile.id_cols or num_col in profile.id_cols):
                    cat_col, num_col = profile.best_bar or (None, None)
            elif profile.best_bar:
                cat_col, num_col = profile.best_bar
            else:
                cat_col = num_col = None

            if cat_col and num_col:
                ax    = fig.add_subplot(gs[cur_row, :2])
                gdata = (df.groupby(cat_col)[num_col].sum()
                          .sort_values(ascending=False).head(15))
                bars  = ax.bar(range(len(gdata)), gdata.values,
                               color=COLORS[:len(gdata)], alpha=0.85,
                               edgecolor="black", linewidth=1.2, width=0.65)
                ax.set_xticks(range(len(gdata)))
                ax.set_xticklabels(gdata.index, rotation=40, ha="right", fontsize=10)
                ax.set_ylabel(num_col, fontsize=12, fontweight="bold", labelpad=10)
                ax.set_title(f"{num_col} by {cat_col}",
                             fontsize=14, fontweight="bold", pad=14)
                ax.grid(True, alpha=0.3, axis="y", linestyle="--", linewidth=0.7)
                ax.set_ylim(0, max(gdata.values) * 1.15)
                for bar in bars:
                    h = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2.0, h,
                            f"{h:,.0f}" if h >= 100 else f"{h:.2f}",
                            ha="center", va="bottom", fontsize=9, fontweight="bold",
                            bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                                      edgecolor="none", alpha=0.8))
                comp_count += 1

        # ── Pie Chart ────────────────────────────────────────────────────
        if config["include_pie_chart"]:
            pie_cat = config["pie_chart_column"] or profile.best_pie
            num_col = profile.numeric[0] if profile.numeric else None
            if pie_cat and num_col and pie_cat not in profile.id_cols:
                ax    = fig.add_subplot(gs[cur_row, 2])
                pdata = df.groupby(pie_cat)[num_col].sum().nlargest(8)
                wedges, texts, autotexts = ax.pie(
                    pdata.values, labels=pdata.index, autopct="%1.1f%%",
                    colors=COLORS[:len(pdata)], startangle=90, pctdistance=0.82,
                    textprops={"fontsize": 9, "fontweight": "bold"},
                    explode=[0.03] * len(pdata))
                for at in autotexts:
                    at.set_color("white"); at.set_fontsize(9); at.set_fontweight("bold")
                ax.set_title(f"{pie_cat} Share of {num_col}",
                             fontsize=13, fontweight="bold", pad=14)
                comp_count += 1

        # ── Line / Trend Chart ───────────────────────────────────────────
        if config["include_line_chart"]:
            if config["line_chart_columns"]:
                lx = config["line_chart_columns"].get("x")
                ly = config["line_chart_columns"].get("y")
            elif profile.best_line:
                lx, ly = profile.best_line
            else:
                lx = ly = None

            if lx and ly and lx not in profile.id_cols and ly not in profile.id_cols and len(df) > 3:
                ax = fig.add_subplot(gs[cur_row + 1, :2])
                # Aggregate if x is categorical/temporal (Month, Quarter, Region…)
                if lx in profile.categorical or lx in profile.temporal:
                    try:
                        trend = df.groupby(lx)[ly].sum()
                        try:
                            trend.index = pd.to_datetime(trend.index)
                            trend = trend.sort_index()
                        except Exception:
                            pass
                        x_vals = range(len(trend))
                        y_vals = trend.values
                        x_lbls = [str(v) for v in trend.index]
                    except Exception:
                        x_vals = range(len(df)); y_vals = df[ly].values; x_lbls = None
                else:
                    x_vals = range(len(df)); y_vals = df[ly].values; x_lbls = None

                ax.plot(x_vals, y_vals, marker="o", linewidth=2.5, markersize=7,
                        color="#4ECDC4", markerfacecolor="#FF6B6B",
                        markeredgecolor="black", markeredgewidth=1.2)
                ax.fill_between(x_vals, y_vals, alpha=0.18, color="#4ECDC4")
                if x_lbls:
                    step = max(1, len(x_lbls) // 12)
                    ax.set_xticks(range(0, len(x_lbls), step))
                    ax.set_xticklabels(x_lbls[::step], rotation=40, ha="right", fontsize=9)
                ax.set_xlabel(lx, fontsize=12, fontweight="bold", labelpad=8)
                ax.set_ylabel(ly, fontsize=12, fontweight="bold", labelpad=8)
                ax.set_title(f"{ly} Trend by {lx}", fontsize=14, fontweight="bold", pad=14)
                ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.7)
                comp_count += 1

        # ── Scatter Plot ─────────────────────────────────────────────────
        if config["include_scatter"]:
            if config["scatter_columns"]:
                sx = config["scatter_columns"].get("x")
                sy = config["scatter_columns"].get("y")
            elif profile.best_scatter:
                sx, sy = profile.best_scatter
            else:
                sx = sy = None

            if sx and sy and sx not in profile.id_cols and sy not in profile.id_cols:
                ax = fig.add_subplot(gs[cur_row + 1, 2])
                ax.scatter(df[sx], df[sy], s=90, alpha=0.6,
                           color="#4ECDC4", edgecolors="#1A1F5E", linewidth=1)
                ax.set_xlabel(sx, fontsize=11, fontweight="bold")
                ax.set_ylabel(sy, fontsize=11, fontweight="bold")
                ax.set_title(f"{sy} vs {sx}", fontsize=13, fontweight="bold", pad=14)
                ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.7)
                comp_count += 1

        # ── Footer ───────────────────────────────────────────────────────
        fig.text(
            0.5, 0.005,
            f"Smart Dashboard  •  {comp_count} chart(s)  •  "
            f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}"
            + (f"  |  Excluded ID cols: {', '.join(profile.id_cols)}" if profile.id_cols else ""),
            ha="center", fontsize=9, style="italic", color="gray",
        )
        plt.tight_layout(rect=[0, 0.02, 1, 0.97])

        # ── Tableau table (stored in session for ui to render after main fig)
        if config.get("include_table"):
            tbl = create_data_table()
            st.session_state["_dashboard_table_fig"] = (
                tbl["figure"] if isinstance(tbl, dict) else None
            )
        else:
            st.session_state.pop("_dashboard_table_fig", None)

        return {
            "type":    "chart",
            "figure":  fig,
            "message": (
                f"Smart dashboard created with {comp_count} chart(s). "
                + (f"Auto-excluded ID columns: {profile.id_cols}. " if profile.id_cols else "")
                + (f"Bar chart: {profile.best_bar}. " if profile.best_bar else "")
                + (f"Pie chart: {profile.best_pie}. "  if profile.best_pie  else "")
                + (f"Line chart: {profile.best_line}." if profile.best_line else "")
            ),
        }

    except Exception as e:
        return f"Error creating dashboard: {e}"
