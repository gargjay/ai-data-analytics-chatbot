"""
tools/chart_tools.py
Individual chart creation tools: bar, pie, line, scatter.
Each returns {"type": "chart", "figure": fig, "message": str} on success.
"""
import streamlit as st
import matplotlib.pyplot as plt

COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#96CEB4", "#F7DC6F", "#BB8FCE"]


def create_bar_chart(group_column, value_column, operation="sum", title=None):
    """Create a bar chart aggregating value_column grouped by group_column."""
    if st.session_state.data is None:
        return "No data loaded"
    df = st.session_state.data
    try:
        ops = {"sum": "sum", "mean": "mean", "count": "count"}
        agg = getattr(df.groupby(group_column)[value_column], ops.get(operation, "sum"))
        data = agg().sort_values(ascending=False)

        fig_w = max(10, len(data) * 1.5)
        fig, ax = plt.subplots(figsize=(fig_w, 7))
        bars = ax.bar(range(len(data)), data.values,
                      color=COLORS[: len(data)], alpha=0.8,
                      edgecolor="black", linewidth=1.5, width=0.7)

        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(data.index, rotation=45, ha="right", fontsize=11)
        ax.set_ylabel(value_column, fontsize=13, fontweight="bold", labelpad=10)
        ax.set_title(title or f"{value_column} by {group_column}",
                     fontsize=15, fontweight="bold", pad=20)
        ax.grid(True, alpha=0.3, axis="y", linestyle="--", linewidth=0.7)
        ax.set_ylim(0, max(data.values) * 1.15)

        for bar in bars:
            h = bar.get_height()
            label = f"{h:,.0f}" if h >= 1000 else f"{h:.1f}"
            ax.text(bar.get_x() + bar.get_width() / 2.0, h, label,
                    ha="center", va="bottom", fontsize=10, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                              edgecolor="none", alpha=0.7))
        plt.tight_layout()
        return {"type": "chart", "figure": fig,
                "message": f"Bar chart created: {operation} of {value_column} by {group_column}"}
    except Exception as e:
        return f"Error creating bar chart: {e}"


def create_pie_chart(column, value_column=None, title=None):
    """Create a pie chart for a categorical column."""
    if st.session_state.data is None:
        return "No data loaded"
    df = st.session_state.data
    try:
        data = (df.groupby(column)[value_column].sum()
                if value_column and value_column in df.columns
                else df[column].value_counts())

        fig, ax = plt.subplots(figsize=(12, 9))
        wedges, texts, autotexts = ax.pie(
            data.values, labels=data.index, autopct="%1.1f%%",
            colors=COLORS[: len(data)], startangle=90,
            pctdistance=0.85,
            textprops={"fontsize": 11, "fontweight": "bold"},
            explode=[0.05] * len(data))
        for at in autotexts:
            at.set_color("white"); at.set_fontsize(11); at.set_fontweight("bold")
        for t in texts:
            t.set_fontsize(12); t.set_fontweight("bold")

        ax.set_title(title or f"{column} Distribution",
                     fontsize=16, fontweight="bold", pad=20)
        plt.tight_layout()
        return {"type": "chart", "figure": fig,
                "message": f"Pie chart created: distribution of {column}"}
    except Exception as e:
        return f"Error creating pie chart: {e}"


def create_line_chart(x_column, y_column, title=None):
    """Create a line chart for y_column over x_column."""
    if st.session_state.data is None:
        return "No data loaded"
    df = st.session_state.data
    try:
        fig, ax = plt.subplots(figsize=(14, 7))
        ax.plot(range(len(df)), df[y_column],
                marker="o", linewidth=3, markersize=10,
                color="#4ECDC4", markerfacecolor="#FF6B6B",
                markeredgecolor="black", markeredgewidth=1.5)
        ax.fill_between(range(len(df)), df[y_column], alpha=0.2, color="#4ECDC4")
        ax.set_xlabel(x_column, fontsize=13, fontweight="bold", labelpad=10)
        ax.set_ylabel(y_column, fontsize=13, fontweight="bold", labelpad=10)
        ax.set_title(title or f"{y_column} over {x_column}",
                     fontsize=15, fontweight="bold", pad=20)
        ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.7)

        if len(df) <= 20:
            ax.set_xticks(range(len(df)))
            ax.set_xticklabels(df[x_column], rotation=45, ha="right", fontsize=10)
        else:
            step = max(1, len(df) // 10)
            ax.set_xticks(range(0, len(df), step))
            ax.set_xticklabels([df[x_column].iloc[i] for i in range(0, len(df), step)],
                               rotation=45, ha="right", fontsize=10)
        if len(df) <= 15:
            for i, val in enumerate(df[y_column]):
                ax.annotate(f"{val:,.0f}" if val >= 100 else f"{val:.1f}",
                            xy=(i, val), xytext=(0, 8), textcoords="offset points",
                            ha="center", fontsize=9, fontweight="bold",
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                                      edgecolor="none", alpha=0.7))
        plt.tight_layout()
        return {"type": "chart", "figure": fig,
                "message": f"Line chart created: {y_column} over {x_column}"}
    except Exception as e:
        return f"Error creating line chart: {e}"


def create_scatter_plot(x_column, y_column, color_column=None, title=None):
    """Create a scatter plot of y_column vs x_column."""
    if st.session_state.data is None:
        return "No data loaded"
    df = st.session_state.data
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        if color_column and color_column in df.columns:
            sc = ax.scatter(df[x_column], df[y_column],
                            c=df[color_column].astype("category").cat.codes,
                            cmap="viridis", s=100, alpha=0.6,
                            edgecolors="black", linewidth=1)
            plt.colorbar(sc, ax=ax, label=color_column)
        else:
            ax.scatter(df[x_column], df[y_column], s=100, alpha=0.6,
                       color="#4ECDC4", edgecolors="black", linewidth=1)
        ax.set_xlabel(x_column, fontsize=12, fontweight="bold")
        ax.set_ylabel(y_column, fontsize=12, fontweight="bold")
        ax.set_title(title or f"{y_column} vs {x_column}",
                     fontsize=14, fontweight="bold", pad=15)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return {"type": "chart", "figure": fig,
                "message": f"Scatter plot created: {y_column} vs {x_column}"}
    except Exception as e:
        return f"Error creating scatter plot: {e}"
