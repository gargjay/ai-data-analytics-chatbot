# 🤖 AI Data Analytics Chatbot

> **An AI-powered conversational analytics application that enables users to analyze CSV and Excel datasets using natural-language queries and generate insights, tables, and visualizations.**

## Overview
The **AI Data Analytics Chatbot** combines Generative AI with Python-based data analytics to simplify dataset exploration. Users can upload structured data and ask questions conversationally, while the AI agent determines and executes the appropriate analytical operation.

## Problem Statement
Traditional data analysis often requires knowledge of Python, SQL, spreadsheet formulas, or BI tools. This project provides a conversational interface that allows users to extract meaningful insights from datasets without manually writing analytical code.

## Dataset
The application supports user-uploaded structured datasets:
* **CSV** (`.csv`)
* **Excel** (`.xlsx`, `.xls`)
Since datasets are uploaded dynamically, the application is not restricted to a single predefined dataset.

## Tools and Technologies
**Python** • **Streamlit** • **OpenAI API** • **Pandas** • **NumPy** • **Matplotlib** • **Seaborn** • **OpenPyXL**
**Concepts:** Generative AI • Agentic AI • LLM Tool Calling • Prompt Engineering • Data Analytics • Data Visualization

## Methods
The application follows an agent-based workflow:
**Upload Dataset → Ask Natural-Language Query → AI Agent Selects Tool → Data Analysis → Generate Response**
The agent can perform dataset inspection, calculations, statistical analysis, aggregations, table generation, and visualization based on the user's request.

## Key Insights
The project demonstrates how LLMs can be integrated with analytical tools to:
* Convert natural-language requests into data-analysis operations
* Automate common analytical workflows
* Generate contextual insights from structured datasets
* Dynamically select appropriate analytical and visualization tools

## Dashboard / Model / Output
Depending on the query, the application can return:
* 💬 Natural-language insights
* 📋 Structured tables
* 📊 Bar, line, pie, and scatter charts
* 🔢 Statistical calculations and aggregations
* 🔍 Dataset and column summaries

## How to Run This Project?
```bash
git clone <your-repository-url>
cd ai-data-analytics-chatbot
pip install -r requirements.txt
streamlit run main.py
```
Configure your **OpenAI API key locally** before running the application. API keys and credentials are intentionally excluded from this repository for security.

## Results & Conclusion
The project provides an interactive approach to data analysis by combining **LLM reasoning with Python analytics tools**, enabling users to explore datasets and generate insights through conversational queries.
It demonstrates practical implementation of **Generative AI, agentic workflows, tool calling, data analytics, and visualization** within a modular Streamlit application.

## Future Work
* Power BI integration
* Advanced statistical analysis
* Automated data-cleaning recommendations
* Multi-file analysis
* Enhanced interactive dashboards
* Cloud deployment and persistent sessions

---
