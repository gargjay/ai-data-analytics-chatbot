"""
tools/powerbi_embed.py

Real Power BI Embedded (Option 2) integration.

Flow
----
1. Authenticate with Azure AD using Client Credentials (app-owns-data model)
   POST https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token

2. Push the uploaded DataFrame as a streaming dataset into a Power BI workspace
   POST https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets

3. Push rows into that dataset
   POST .../datasets/{dataset_id}/tables/{table_name}/rows

4. Create a report on top of that dataset (optional auto-report)
   POST .../groups/{workspace_id}/reports  (clone from a template report if available)

5. Generate an Embed Token for the report
   POST https://api.powerbi.com/v1.0/myorg/GenerateToken

6. Return the embed URL + token so the UI can render the iframe.

Credentials required (stored in st.session_state.pbi_creds):
    tenant_id      – Azure AD tenant (Directory) ID
    client_id      – App Registration (Application) ID
    client_secret  – App Registration client secret
    workspace_id   – Power BI workspace (group) ID  a.k.a. group_id

All of these are obtainable for free from:
  - Azure Portal → App Registrations
  - Power BI → Workspace Settings
"""

import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

# ── Constants ────────────────────────────────────────────────────────────────
AUTHORITY_URL  = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
PBI_SCOPE      = "https://analysis.windows.net/powerbi/api/.default"
PBI_BASE       = "https://api.powerbi.com/v1.0/myorg"
PBI_TABLE_NAME = "DataTable"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_creds() -> dict:
    """Return Power BI credentials from session state or raise."""
    creds = st.session_state.get("pbi_creds", {})
    missing = [k for k in ("tenant_id", "client_id", "client_secret", "workspace_id")
               if not creds.get(k)]
    if missing:
        raise ValueError(
            f"Missing Power BI credentials: {', '.join(missing)}. "
            "Please enter them in the sidebar under '⚡ Power BI Embedded'."
        )
    return creds


def _get_access_token(creds: dict) -> str:
    """Obtain an Azure AD bearer token via client credentials flow."""
    url  = AUTHORITY_URL.format(tenant_id=creds["tenant_id"])
    body = {
        "grant_type":    "client_credentials",
        "client_id":     creds["client_id"],
        "client_secret": creds["client_secret"],
        "scope":         PBI_SCOPE,
    }
    resp = requests.post(url, data=body, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Azure AD auth failed ({resp.status_code}): {resp.text}"
        )
    return resp.json()["access_token"]


def _pbi_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _df_to_pbi_schema(df: pd.DataFrame) -> list:
    """Convert DataFrame dtypes to Power BI column type strings."""
    TYPE_MAP = {
        "int64":          "Int64",
        "int32":          "Int64",
        "float64":        "Double",
        "float32":        "Double",
        "bool":           "Boolean",
        "datetime64[ns]": "DateTime",
        "object":         "String",
        "category":       "String",
    }
    columns = []
    for col in df.columns:
        dtype_str = str(df[col].dtype)
        pbi_type  = TYPE_MAP.get(dtype_str, "String")
        columns.append({"name": col, "dataType": pbi_type})
    return columns


def _create_push_dataset(token: str, workspace_id: str,
                          df: pd.DataFrame, dataset_name: str) -> str:
    """
    Create (or recreate) a push dataset in the workspace.
    Returns the new dataset_id.
    """
    headers = _pbi_headers(token)
    url     = f"{PBI_BASE}/groups/{workspace_id}/datasets"

    payload = {
        "name":                dataset_name,
        "defaultMode":         "Push",
        "tables": [
            {
                "name":    PBI_TABLE_NAME,
                "columns": _df_to_pbi_schema(df),
            }
        ],
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Failed to create Power BI dataset ({resp.status_code}): {resp.text}"
        )
    return resp.json()["id"]


def _push_rows(token: str, workspace_id: str,
               dataset_id: str, df: pd.DataFrame) -> None:
    """Push DataFrame rows into the dataset table in batches of 9,999 (API limit)."""
    headers  = _pbi_headers(token)
    url      = (f"{PBI_BASE}/groups/{workspace_id}/datasets/"
                f"{dataset_id}/tables/{PBI_TABLE_NAME}/rows")

    # Convert DataFrame to list of dicts; handle NaN and Timestamps
    records = json.loads(df.to_json(orient="records", date_format="iso"))

    BATCH = 9_999
    for start in range(0, len(records), BATCH):
        batch   = records[start: start + BATCH]
        payload = {"rows": batch}
        resp    = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Failed to push rows ({resp.status_code}): {resp.text}"
            )


def _get_or_create_report(token: str, workspace_id: str,
                           dataset_id: str, report_name: str) -> tuple[str, str]:
    """
    Check if a report with report_name already exists in the workspace.
    If it does, return its (report_id, embed_url).
    If not, raise informative error — auto-creating requires a template in the workspace.
    Returns (report_id, embed_url).
    """
    headers = _pbi_headers(token)
    url     = f"{PBI_BASE}/groups/{workspace_id}/reports"
    resp    = requests.get(url, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Failed to list reports ({resp.status_code}): {resp.text}"
        )

    reports = resp.json().get("value", [])

    # Try to find an existing report linked to this dataset or with this name
    for r in reports:
        if r.get("name") == report_name or r.get("datasetId") == dataset_id:
            return r["id"], r["embedUrl"]

    # No existing report — we need to create one by cloning a blank template
    # Power BI REST doesn't support creating a report from scratch (only via .pbix upload
    # or clone). We signal this clearly so the user knows what to do.
    raise RuntimeError(
        "No report found for this dataset. Please create a report manually in Power BI Service "
        "by connecting to the pushed dataset, then re-run. The dataset has been pushed successfully."
    )


def _generate_embed_token(token: str, workspace_id: str,
                           report_id: str, dataset_id: str) -> str:
    """Generate a short-lived embed token for the report."""
    headers = _pbi_headers(token)
    url     = f"{PBI_BASE}/GenerateToken"
    payload = {
        "reports":  [{"id": report_id}],
        "datasets": [{"id": dataset_id}],
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Failed to generate embed token ({resp.status_code}): {resp.text}"
        )
    return resp.json()["token"]


# ── Public function called by the agent tool ──────────────────────────────────

def embed_powerbi_report(report_name: str = None) -> dict:
    """
    Full end-to-end Power BI Embedded flow:
      1. Authenticate with Azure AD
      2. Push the loaded DataFrame as a dataset
      3. Push all rows
      4. Find the linked report (or instruct user to create one)
      5. Generate embed token
      6. Return embed_url + token for iframe rendering

    Returns
    -------
    dict with keys:
        type        : "powerbi_embed"
        embed_url   : str   — the Power BI embed URL
        token       : str   — the embed access token
        dataset_id  : str
        report_id   : str
        message     : str   — human-readable status
    OR a plain error string if anything fails.
    """
    if st.session_state.data is None:
        return "No data loaded. Please upload a file first."

    df   = st.session_state.data
    name = report_name or f"AI_Dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        creds        = _get_creds()
        workspace_id = creds["workspace_id"]

        # Step 1 — Auth
        token = _get_access_token(creds)

        # Step 2 — Create dataset
        dataset_id = _create_push_dataset(token, workspace_id, df, name)

        # Step 3 — Push rows
        _push_rows(token, workspace_id, dataset_id, df)

        # Step 4 — Find report
        report_id, embed_url = _get_or_create_report(
            token, workspace_id, dataset_id, name)

        # Step 5 — Embed token
        embed_token = _generate_embed_token(
            token, workspace_id, report_id, dataset_id)

        # Persist for UI rendering
        st.session_state["_pbi_embed"] = {
            "embed_url":  embed_url,
            "token":      embed_token,
            "dataset_id": dataset_id,
            "report_id":  report_id,
            "name":       name,
            "rows":       len(df),
            "cols":       len(df.columns),
        }

        return {
            "type":       "powerbi_embed",
            "embed_url":  embed_url,
            "token":      embed_token,
            "dataset_id": dataset_id,
            "report_id":  report_id,
            "message": (
                f"✅ Power BI report '{name}' embedded successfully. "
                f"{len(df):,} rows × {len(df.columns)} columns pushed. "
                f"Report is rendering in the Power BI iframe below."
            ),
        }

    except Exception as e:
        return f"Power BI Embedded error: {e}"
