"""
ui/chat_interface.py
Renders the chat history and handles user input → agent → display cycle.
"""
import streamlit as st
import matplotlib.pyplot as plt

from agent.agent_loop import run_agent


def render_chat(api_key: str):
    """Display chat history and handle new user messages."""

    # ── Chat history ─────────────────────────────────────────────────────
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            for fig in msg.get("figures", []):
                st.pyplot(fig)

    # ── New message ───────────────────────────────────────────────────────
    if prompt := st.chat_input("Ask about your data or configure the dashboard…"):

        st.session_state.chat_history.append({"role": "user", "content": prompt, "figures": []})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking…"):
                try:
                    final_text, figures = run_agent(prompt, api_key)

                    # Display text answer
                    if final_text:
                        st.write(final_text)

                    # Display every figure produced
                    for fig in figures:
                        st.pyplot(fig)

                    # Persist to history (store figures for re-render)
                    st.session_state.chat_history.append({
                        "role":    "assistant",
                        "content": final_text,
                        "figures": figures,
                    })

                    plt.close("all")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Agent error: {e}")
