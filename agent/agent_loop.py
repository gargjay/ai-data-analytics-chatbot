"""
agent/agent_loop.py
Runs the OpenAI GPT-4o agent loop:
  1. Sends user prompt + system prompt + tool definitions
  2. Executes tool calls returned by the model
  3. Collects figures to render and the final text answer
Returns (final_text, list_of_figures)
"""
import json
import streamlit as st
from openai import OpenAI

from agent.system_prompt import build_system_prompt
from agent.tool_definitions import TOOLS, get_available_functions


def run_agent(prompt: str, api_key: str):
    """
    Run the agent loop for a single user prompt.

    Returns
    -------
    final_text : str
        The model's final plain-text response.
    figures : list
        List of matplotlib Figure objects to render (in order).
    """
    client     = OpenAI(api_key=api_key)
    avail_fns  = get_available_functions()

    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user",   "content": prompt},
    ]

    figures     = []   # collect all figures produced during this turn
    final_text  = ""

    for _ in range(8):   # max iterations
        response         = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        resp_msg = response.choices[0].message

        # ── Model called one or more tools ───────────────────────────────
        if resp_msg.tool_calls:
            messages.append(resp_msg)

            for tc in resp_msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)

                if fn_name not in avail_fns:
                    tool_result = f"Unknown tool: {fn_name}"
                else:
                    result = avail_fns[fn_name](**fn_args)

                    # Extract figure if the tool returned one
                    if isinstance(result, dict) and result.get("type") == "chart":
                        figures.append(result["figure"])
                        tool_result = result["message"]
                    else:
                        tool_result = str(result)

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "name":         fn_name,
                    "content":      tool_result,
                })

        # ── Model gave a final text answer ───────────────────────────────
        else:
            final_text = resp_msg.content or ""
            break

    # If table was stored separately by dashboard (side-channel)
    tbl_fig = st.session_state.pop("_dashboard_table_fig", None)
    if tbl_fig is not None:
        figures.append(tbl_fig)

    return final_text, figures
