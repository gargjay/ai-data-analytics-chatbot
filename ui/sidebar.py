"""
ui/sidebar.py
Renders the Streamlit sidebar: API key input, file uploader,
dashboard config summary, and data preview.
"""
import streamlit as st
import pandas as pd


def render_sidebar():
    """
    Render the full sidebar and return (api_key, uploaded_file).
    Loads data into st.session_state.data on successful upload.
    """
    with st.sidebar:
        st.header("⚙️ Settings")

        # ── API Key ──────────────────────────────────────────────────────
        api_key = st.text_input("OpenAI API Key", type="password",
                                placeholder="sk-...")
        if api_key:
            st.success("✅ API key set")
        else:
            st.warning("⚠️ Enter your OpenAI API key")

        st.divider()

        # ── File Upload ──────────────────────────────────────────────────
        st.subheader("📁 Upload Data")
        uploaded_file = st.file_uploader(
            "Excel / CSV", type=["xlsx", "xls", "csv"])

        if uploaded_file and api_key:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                st.session_state.data = df
                st.success(f"✅ Loaded: {uploaded_file.name}")
                st.info(f"📊 {df.shape[0]} rows × {df.shape[1]} cols")

                # ── Dashboard config summary ─────────────────────────────
                st.divider()
                st.subheader("📊 Dashboard Config")
                config = st.session_state.get("dashboard_config", {})
                checks = [
                    ("include_kpis",       "KPI Cards"),
                    ("include_bar_chart",  "Bar Chart"),
                    ("include_pie_chart",  "Pie Chart"),
                    ("include_line_chart", "Line Chart"),
                    ("include_scatter",    "Scatter Plot"),
                    ("include_table",      "Tableau Table"),
                ]
                st.write("Currently included:")
                for key, label in checks:
                    if config.get(key):
                        st.write(f"✅ {label}")

                # ── Data preview ─────────────────────────────────────────
                with st.expander("📋 View Data (first 10 rows)"):
                    st.dataframe(df.head(10))

            except Exception as e:
                st.error(f"Error loading file: {e}")
        elif not api_key:
            st.warning("⚠️ Enter API key above first")

    return api_key, uploaded_file
