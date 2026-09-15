"""
ui/welcome.py
Welcome / instructions screen shown when no data is loaded yet.
"""
import streamlit as st


def render_welcome():
    st.info("👆 Upload a data file and enter your OpenAI API key to get started!")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 🎯 What you can do:
        - **Ask questions** about your data in plain English
        - **Create charts** — bar, pie, line, scatter
        - **Generate a Tableau-style summary table** for all columns
        - **Configure & build** a custom multi-chart dashboard
        """)

    with col2:
        st.markdown("""
        ### 💬 Example commands:
        - *"Create a bar chart of Sales by Region"*
        - *"What is the highest Revenue?"*
        - *"Give me a summary table of all columns"*
        - *"Add scatter plot to dashboard, then show dashboard"*
        - *"Remove pie chart from dashboard"*
        - *"Show dashboard configuration"*
        - *"Reset dashboard to default"*
        """)
