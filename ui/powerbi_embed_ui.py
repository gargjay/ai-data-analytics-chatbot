"""
ui/powerbi_embed_ui.py

Renders an embedded Power BI report inside Streamlit using
st.components.v1.html() with the Power BI JavaScript SDK.

The SDK approach (powerbi-client) is the officially recommended way to embed
Power BI reports — it handles token injection, resizing, and event hooks
entirely in the browser without exposing the embed token in the iframe src URL.

Reference: https://learn.microsoft.com/en-us/javascript/api/overview/powerbi/
"""
import streamlit as st
import streamlit.components.v1 as components


# Height of the embedded report in pixels
EMBED_HEIGHT_PX = 700


def render_powerbi_embed(embed_info: dict) -> None:
    """
    Render a Power BI report embed using the Power BI JavaScript Client SDK.

    Parameters
    ----------
    embed_info : dict
        Must contain:
            embed_url  — the embedUrl from the Power BI REST API
            token      — the embed token from GenerateToken
            report_id  — the Power BI report GUID
            name       — display name shown above the iframe
            rows       — row count (for the info banner)
            cols       — column count (for the info banner)
    """
    embed_url  = embed_info["embed_url"]
    token      = embed_info["token"]
    report_id  = embed_info["report_id"]
    name       = embed_info.get("name", "Power BI Report")
    rows       = embed_info.get("rows", "?")
    cols       = embed_info.get("cols", "?")

    # ── Info banner ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, #1B1A19 0%, #252423 100%);
        border-left: 5px solid #F2C811;
        padding: 12px 18px;
        border-radius: 4px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 14px;
    ">
        <span style="font-size:28px;">⚡</span>
        <div>
            <div style="color:#F2C811; font-weight:700; font-size:15px;">
                Power BI Embedded Report — {name}
            </div>
            <div style="color:#CAC7C4; font-size:12px; margin-top:3px;">
                {rows:,} rows · {cols} columns · Live data pushed via Power BI REST API
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Power BI JavaScript SDK embed ────────────────────────────────────────
    # The SDK is loaded from Microsoft's CDN.
    # It takes the embedUrl + accessToken and renders the full interactive report
    # (filters, drill-down, cross-filtering, tooltips, page navigation — everything
    #  that works in Power BI Service works here).
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background: #FAF9F8; font-family: 'Segoe UI', sans-serif; }}

            #pbi-container {{
                width: 100%;
                height: {EMBED_HEIGHT_PX}px;
                border: 2px solid #F2C811;
                border-radius: 4px;
                overflow: hidden;
                position: relative;
            }}

            #loading-overlay {{
                position: absolute;
                inset: 0;
                background: #1B1A19;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                color: #F2C811;
                font-size: 16px;
                font-weight: 600;
                gap: 16px;
                z-index: 10;
                transition: opacity 0.4s ease;
            }}

            .spinner {{
                width: 48px; height: 48px;
                border: 5px solid #333;
                border-top-color: #F2C811;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }}

            @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

            #error-box {{
                display: none;
                position: absolute;
                inset: 0;
                background: #1B1A19;
                color: #E05959;
                padding: 32px;
                font-size: 14px;
                white-space: pre-wrap;
                z-index: 20;
            }}

            iframe {{
                width: 100% !important;
                height: 100% !important;
                border: none;
            }}
        </style>

        <!-- Power BI JavaScript Client SDK (official Microsoft CDN) -->
        <script src="https://cdn.jsdelivr.net/npm/powerbi-client@2.22.3/dist/powerbi.min.js"></script>
    </head>
    <body>
        <div id="pbi-container">
            <div id="loading-overlay">
                <div class="spinner"></div>
                <div>Connecting to Power BI…</div>
            </div>
            <div id="error-box"></div>
        </div>

        <script>
            const embedConfig = {{
                type:        'report',
                id:          '{report_id}',
                embedUrl:    '{embed_url}',
                accessToken: '{token}',
                tokenType:   window.powerbi ? powerbi.models.TokenType.Embed : 1,
                settings: {{
                    navContentPaneEnabled: true,
                    filterPaneEnabled:     true,
                    background:            0,   // transparent
                }},
            }};

            const container = document.getElementById('pbi-container');
            const overlay   = document.getElementById('loading-overlay');
            const errorBox  = document.getElementById('error-box');

            try {{
                const report = powerbi.embed(container, embedConfig);

                report.on('loaded', function () {{
                    overlay.style.opacity = '0';
                    setTimeout(() => overlay.style.display = 'none', 400);
                }});

                report.on('error', function (event) {{
                    overlay.style.display = 'none';
                    errorBox.style.display = 'block';
                    errorBox.innerText = (
                        '⚠️  Power BI Embed Error\\n\\n' +
                        JSON.stringify(event.detail, null, 2)
                    );
                }});

            }} catch (err) {{
                overlay.style.display = 'none';
                errorBox.style.display = 'block';
                errorBox.innerText = '⚠️  SDK Error: ' + err.message;
            }}
        </script>
    </body>
    </html>
    """

    components.html(html_code, height=EMBED_HEIGHT_PX + 10, scrolling=False)


def render_pbi_setup_guide() -> None:
    """
    Show a collapsible step-by-step setup guide for first-time users.
    Displayed in the sidebar when credentials are not yet entered.
    """
    with st.expander("📖 How to get your credentials", expanded=False):
        st.markdown("""
**Step 1 — Register an Azure AD App**
1. Go to [portal.azure.com](https://portal.azure.com) → **Azure Active Directory → App Registrations → New Registration**
2. Name it anything (e.g. `StreamlitPBI`)
3. Copy the **Application (client) ID** → `Client ID`
4. Copy the **Directory (tenant) ID** → `Tenant ID`
5. Go to **Certificates & Secrets → New client secret** → copy the value → `Client Secret`

**Step 2 — Grant Power BI API permissions**
1. In the same App Registration → **API Permissions → Add permission → Power BI Service**
2. Add: `Dataset.ReadWrite.All`, `Report.ReadWrite.All`, `Workspace.Read.All`
3. Click **Grant admin consent**

**Step 3 — Add the App to your Power BI Workspace**
1. In [app.powerbi.com](https://app.powerbi.com) → open your workspace → **Access**
2. Add your App Registration by name, set role to **Contributor**
3. Copy the workspace URL — the GUID after `/groups/` is your **Workspace ID**

**Step 4 — Enable Service Principal in Power BI Admin**
1. Go to [app.powerbi.com/admin-portal](https://app.powerbi.com/admin-portal)
2. **Tenant settings → Developer settings → Allow service principals to use Power BI APIs** → Enable

After entering all four credentials, type **"embed power bi report"** in the chat.
        """)
