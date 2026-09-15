"""
tools/data_tools.py
Basic data query tools: info, statistics, calculation, group-by.
"""
import streamlit as st


def get_data_info():
    """Get information about the loaded dataset."""
    if st.session_state.data is None:
        return "No data loaded"
    df = st.session_state.data
    info = [
        f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
        f"Columns: {list(df.columns)}",
        f"\nFirst 5 rows:\n{df.head().to_string()}",
    ]
    return "\n".join(info)


def calculate_statistics(column, operation):
    """Calculate a statistic for a single numeric column."""
    if st.session_state.data is None:
        return "No data loaded"
    df = st.session_state.data
    if column not in df.columns:
        return f"Column '{column}' not found. Available: {list(df.columns)}"
    try:
        ops = {
            "mean":   df[column].mean,
            "median": df[column].median,
            "sum":    df[column].sum,
            "min":    df[column].min,
            "max":    df[column].max,
            "count":  df[column].count,
            "std":    df[column].std,
        }
        if operation not in ops:
            return f"Unknown operation: {operation}"
        result = ops[operation]()
        return f"The {operation} of {column} is: {result:.2f}"
    except Exception as e:
        return f"Error: {e}"


def perform_calculation(expression):
    """Safely evaluate a simple arithmetic expression."""
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Error in calculation: {e}"


def group_and_aggregate(group_column, value_column, operation):
    """Group data by a column and apply an aggregation."""
    if st.session_state.data is None:
        return "No data loaded"
    df = st.session_state.data
    try:
        ops = {
            "sum":   df.groupby(group_column)[value_column].sum,
            "mean":  df.groupby(group_column)[value_column].mean,
            "count": df.groupby(group_column)[value_column].count,
            "max":   df.groupby(group_column)[value_column].max,
            "min":   df.groupby(group_column)[value_column].min,
        }
        if operation not in ops:
            return f"Unknown operation: {operation}"
        result = ops[operation]()
        return f"Results grouped by {group_column}:\n{result.to_string()}"
    except Exception as e:
        return f"Error: {e}"


def answer_question(question):
    """Answer a general natural-language question about the data."""
    if st.session_state.data is None:
        return "No data loaded to analyze"
    df = st.session_state.data
    q = question.lower()
    numeric_cols     = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
    try:
        if any(w in q for w in ["highest", "maximum", "most", "top"]):
            if numeric_cols and categorical_cols:
                grp = df.groupby(categorical_cols[0])[numeric_cols[0]].sum()
                return f"The highest {categorical_cols[0]} is {grp.idxmax()} with {grp.max():,.2f}"
        if any(w in q for w in ["lowest", "minimum", "least", "bottom"]):
            if numeric_cols and categorical_cols:
                grp = df.groupby(categorical_cols[0])[numeric_cols[0]].sum()
                return f"The lowest {categorical_cols[0]} is {grp.idxmin()} with {grp.min():,.2f}"
        if any(w in q for w in ["total", "sum"]):
            if numeric_cols:
                return f"The total {numeric_cols[0]} is {df[numeric_cols[0]].sum():,.2f}"
        if any(w in q for w in ["average", "mean"]):
            if numeric_cols:
                return f"The average {numeric_cols[0]} is {df[numeric_cols[0]].mean():,.2f}"
        if any(w in q for w in ["count", "how many"]):
            if categorical_cols:
                return f"There are {df[categorical_cols[0]].nunique()} unique {categorical_cols[0]} values"
        return "I can answer questions like: highest, lowest, total, average, or count values in your data."
    except Exception as e:
        return f"Error answering question: {e}"
