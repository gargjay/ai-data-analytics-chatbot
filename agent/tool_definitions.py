"""
agent/tool_definitions.py
OpenAI function-calling tool schemas for every tool in the app.
Import `TOOLS` and `get_available_functions()` in the agent loop.
"""
from tools.data_tools import (
    get_data_info, calculate_statistics,
    perform_calculation, group_and_aggregate, answer_question,
)
from tools.chart_tools import (
    create_bar_chart, create_pie_chart,
    create_line_chart, create_scatter_plot,
)
from tools.table_tool import create_data_table
from tools.dashboard_tools import (
    configure_dashboard, show_dashboard_config,
    reset_dashboard_config, create_custom_dashboard,
)

# ── Tool schemas ────────────────────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_data_info",
            "description": "Get basic information about the loaded dataset (shape, columns, sample rows).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_statistics",
            "description": "Calculate a single statistic (mean, median, sum, min, max, count, std) for one column.",
            "parameters": {
                "type": "object",
                "properties": {
                    "column":    {"type": "string"},
                    "operation": {"type": "string",
                                  "enum": ["mean","median","sum","min","max","count","std"]},
                },
                "required": ["column", "operation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "perform_calculation",
            "description": "Evaluate a simple arithmetic expression (e.g. '100 * 2 + 50').",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "group_and_aggregate",
            "description": "Group data by a categorical column and aggregate a numeric column.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_column": {"type": "string"},
                    "value_column": {"type": "string"},
                    "operation":    {"type": "string",
                                     "enum": ["sum","mean","count","max","min"]},
                },
                "required": ["group_column", "value_column", "operation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_bar_chart",
            "description": "Create a bar chart. Requires knowing a categorical and a numeric column.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_column":  {"type": "string"},
                    "value_column":  {"type": "string"},
                    "operation":     {"type": "string", "enum": ["sum","mean","count"]},
                    "title":         {"type": "string"},
                },
                "required": ["group_column", "value_column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_pie_chart",
            "description": "Create a pie/donut chart showing distribution of a categorical column.",
            "parameters": {
                "type": "object",
                "properties": {
                    "column":       {"type": "string"},
                    "value_column": {"type": "string"},
                    "title":        {"type": "string"},
                },
                "required": ["column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_line_chart",
            "description": "Create a line chart showing a numeric column over another column.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x_column": {"type": "string"},
                    "y_column": {"type": "string"},
                    "title":    {"type": "string"},
                },
                "required": ["x_column", "y_column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_scatter_plot",
            "description": "Create a scatter plot of two numeric columns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x_column":     {"type": "string"},
                    "y_column":     {"type": "string"},
                    "color_column": {"type": "string"},
                    "title":        {"type": "string"},
                },
                "required": ["x_column", "y_column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_data_table",
            "description": (
                "Create a Tableau-style summary table covering ALL columns in the dataset. "
                "Shows Total, Average, Median, Min, Max, Std Dev, Count, Nulls for numeric columns; "
                "Count, Unique, Most-Frequent, Frequency, Nulls for categorical columns. "
                "ALWAYS call this when the user asks for a 'table', 'tableau table', "
                "'summary table', 'data table', 'column stats', 'column summary', "
                "or any variation. No arguments required."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Optional custom title"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "configure_dashboard",
            "description": (
                "Toggle or configure dashboard components. Use when the user says things like "
                "'remove bar chart', 'add scatter plot', 'include the tableau table in dashboard', "
                "'change bar chart columns', etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "include_kpis":    {"type": "boolean"},
                    "include_bar":     {"type": "boolean"},
                    "include_pie":     {"type": "boolean"},
                    "include_line":    {"type": "boolean"},
                    "include_scatter": {"type": "boolean"},
                    "include_table":   {"type": "boolean",
                                        "description": "Include Tableau summary table in the dashboard"},
                    "bar_columns": {
                        "type": "object",
                        "description": "e.g. {\"category\": \"Region\", \"value\": \"Sales\"}",
                        "properties": {
                            "category": {"type": "string"},
                            "value":    {"type": "string"},
                        },
                    },
                    "pie_column":     {"type": "string"},
                    "line_columns":   {
                        "type": "object",
                        "properties": {"x": {"type": "string"}, "y": {"type": "string"}},
                    },
                    "scatter_columns": {
                        "type": "object",
                        "properties": {"x": {"type": "string"}, "y": {"type": "string"}},
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "show_dashboard_config",
            "description": "Show the current dashboard configuration (which components are on/off).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset_dashboard_config",
            "description": "Reset the dashboard to its default configuration.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_custom_dashboard",
            "description": (
                "Render/show the dashboard using the current configuration. "
                "Call after configuring, or when the user says 'show dashboard', "
                "'generate dashboard', 'build dashboard'."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "answer_question",
            "description": "Answer a general natural-language question about the data.",
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        },
    },
]

# ── Function registry ───────────────────────────────────────────────────────
def get_available_functions():
    return {
        "get_data_info":          get_data_info,
        "calculate_statistics":   calculate_statistics,
        "perform_calculation":    perform_calculation,
        "group_and_aggregate":    group_and_aggregate,
        "create_bar_chart":       create_bar_chart,
        "create_pie_chart":       create_pie_chart,
        "create_line_chart":      create_line_chart,
        "create_scatter_plot":    create_scatter_plot,
        "create_data_table":      create_data_table,
        "configure_dashboard":    configure_dashboard,
        "show_dashboard_config":  show_dashboard_config,
        "reset_dashboard_config": reset_dashboard_config,
        "create_custom_dashboard": create_custom_dashboard,
        "answer_question":        answer_question,
    }
