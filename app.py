# -*- coding: utf-8 -*-
"""
Streamlit UI ? Power BI Governance Agent (Phase 1 + Phase 2 Scanner)
Run: streamlit run app.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import time
from agent import run_governance_scan

st.set_page_config(page_title="Power BI Governance Agent", page_icon="*", layout="wide")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
  html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
  .main { background: #0d1117; color: #e6edf3; }
  .header-block { background: linear-gradient(135deg,#1a1f2e 0%,#0d1117 100%); border:1px solid #30363d; border-left:4px solid #f7c948; padding:24px 28px; border-radius:8px; margin-bottom:24px; }
  .header-block h1 { font-family:'IBM Plex Mono',monospace; font-size:1.4rem; color:#f7c948; margin:0 0 4px 0; }
  .header-block p { color:#8b949e; margin:0; font-size:.9rem; }
  .step-log { background:#0d1117; border:1px solid #21262d; border-radius:6px; padding:12px 16px; font-family:'IBM Plex Mono',monospace; font-size:.8rem; color:#8b949e; max-height:240px; overflow-y:auto; }
  .step-log .tool_call { color:#58a6ff; }
  .step-log .tool_result { color:#3fb950; }
  .step-log .start { color:#f7c948; }
  .step-log .complete { color:#3fb950; font-weight:600; }
  .step-log .error { color:#f85149; }
  .report-box { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:28px; font-size:.95rem; line-height:1.7; color:#e6edf3; }
  .metric-card { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px 20px; text-align:center; }
  .metric-card .num { font-family:'IBM Plex Mono',monospace; font-size:2rem; font-weight:600; color:#f7c948; }
  .metric-card .label { font-size:.8rem; color:#8b949e; margin-top:4px; }
  .stButton > button { background:#f7c948; color:#0d1117; font-family:'IBM Plex Mono',monospace; font-weight:600; border:none; padding:10px 28px; border-radius:6px; font-size:.9rem; width:100%; }
  .stButton > button:hover { background:#ffd966; }
  .api-notice { background:#1a1f2e; border:1px solid #30363d; border-left:3px solid #58a6ff; padding:12px 16px; border-radius:6px; font-size:.85rem; color:#8b949e; }
  .mode-badge { display:inline-block; padding:2px 10px; border-radius:12px; font-size:.75rem; font-family:'IBM Plex Mono',monospace; font-weight:600; margin-bottom:8px; }
  .mode-gov  { background:#1a2a1a; color:#3fb950; border:1px solid #3fb950; }
  .mode-scan { background:#1a1f2e; color:#58a6ff; border:1px solid #58a6ff; }
  div[data-testid="stTextArea"] textarea { background:#161b22; color:#e6edf3; border:1px solid #30363d; font-family:'IBM Plex Mono',monospace; font-size:.85rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-block">
  <h1>* POWER BI GOVERNANCE AGENT</h1>
  <p>Phase 1: Governance scan &nbsp;?&nbsp; Phase 2: Scanner API ? lineage &amp; impact analysis &nbsp;?&nbsp; Mock Power BI REST API data</p>
</div>
""", unsafe_allow_html=True)

# ?? API key ????????????????????????????????????????????????????????????????????
col_key, _ = st.columns([2, 1])
with col_key:
    api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key

st.markdown('<div class="api-notice">? <strong>Learning prototype</strong> ? mock Power BI data, no real tenant needed. Get a free key at <a href="https://console.anthropic.com" style="color:#58a6ff">console.anthropic.com</a></div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ?? Mode selector ??????????????????????????????????????????????????????????????
mode = st.radio(
    "Scan mode",
    ["[P1]  Phase 1 ? Governance Scan", "[P2]  Phase 2 ? Scanner API (Lineage + Impact)"],
    horizontal=True
)

PRESETS = {
    "[P1]  Phase 1 ? Governance Scan": [
        ("Full governance audit",
         "Run a full Power BI governance audit. Check for stale workspaces (90+ days inactive), orphaned workspaces (no users), empty workspaces (no content), and stale datasets (90+ days since refresh). Produce a prioritised governance report."),
        ("Stale assets only",
         "Check only for stale workspaces and stale datasets. Flag anything inactive for 60 or more days. List recommendations."),
        ("Gateway & datasource audit",
         "List all gateway clusters and their registered datasources. For each stale or empty workspace, check if its datasets still reference an active gateway datasource. Highlight any orphaned gateway connections."),
    ],
    "[P2]  Phase 2 ? Scanner API (Lineage + Impact)": [
        ("Full lineage scan",
         "Run the full 4-step Scanner API flow (GetModifiedWorkspaces ? PostWorkspaceInfo ? GetScanStatus ? GetScanResult). Then for each dataset, retrieve its full lineage chain. Produce a lineage and impact report."),
        ("Impact analysis: sql-prod-01",
         "Run the Scanner API flow, then perform impact analysis for the server 'sql-prod-01'. Show every dataset and report that would be affected if that server changed."),
        ("Compliance: sensitivity labels",
         "Run the Scanner API scan, then flag all datasets and reports missing a sensitivity label. Also flag all uncertified datasets. Produce a compliance report."),
    ]
}

selected_mode_presets = PRESETS[mode]

col_preset, col_custom = st.columns([1, 2])
with col_preset:
    preset_names = [p[0] for p in selected_mode_presets]
    chosen = st.selectbox("Quick presets", preset_names)
    preset_task = next(p[1] for p in selected_mode_presets if p[0] == chosen)

with col_custom:
    task_input = st.text_area("Task (edit freely)", value=preset_task, height=110)

col_run, _ = st.columns([1, 3])
with col_run:
    run_clicked = st.button("?  RUN SCAN", use_container_width=True)

st.markdown("---")

# ?? Run ????????????????????????????????????????????????????????????????????????
if run_clicked:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.error("?? Please enter your Anthropic API key above.")
        st.stop()

    st.markdown("**Agent activity log**")
    log_placeholder = st.empty()
    log_lines = []

    def update_log(step_type, message):
        clean = message.replace("[TOOL]", "").replace("?", "  ?").replace("[SCAN]", "").replace("[OK]", "").strip()
        log_lines.append(f'<div class="{step_type}">{clean}</div>')
        log_placeholder.markdown(f'<div class="step-log">{"".join(log_lines)}</div>', unsafe_allow_html=True)

    with st.spinner("Agent running..."):
        result = run_governance_scan(task=task_input, on_step=update_log)

    st.markdown("<br>", unsafe_allow_html=True)

    # Metrics — row 1: agent activity
    tools_called = result["tools_called"]
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="num">{result["iterations"]}</div><div class="label">Iterations</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="num">{len(tools_called)}</div><div class="label">API calls made</div></div>', unsafe_allow_html=True)
    with m3:
        scanner_calls = sum(1 for t in tools_called if t["tool"].startswith("scanner_"))
        st.markdown(f'<div class="metric-card"><div class="num">{scanner_calls}</div><div class="label">Scanner API calls</div></div>', unsafe_allow_html=True)
    with m4:
        unique = len(set(t["tool"] for t in tools_called))
        st.markdown(f'<div class="metric-card"><div class="num">{unique}</div><div class="label">Unique tools used</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Metrics — row 2: token usage
    t1, t2, t3, _ = st.columns(4)
    with t1:
        st.markdown(f'<div class="metric-card"><div class="num">{result["input_tokens"]:,}</div><div class="label">Input tokens</div></div>', unsafe_allow_html=True)
    with t2:
        st.markdown(f'<div class="metric-card"><div class="num">{result["output_tokens"]:,}</div><div class="label">Output tokens</div></div>', unsafe_allow_html=True)
    with t3:
        st.markdown(f'<div class="metric-card"><div class="num">{result["total_tokens"]:,}</div><div class="label">Total tokens</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("**Report**")
    st.markdown(f'<div class="report-box">{result["report"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    st.download_button(
        "Download  Download Report (.txt)",
        data=result["report"],
        file_name=f"pbi_governance_{time.strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )

    with st.expander("[TOOL] Tools called (full detail)"):
        for i, t in enumerate(tools_called, 1):
            prefix = "[P2] scanner" if t["tool"].startswith("scanner_") else "[P1] governance"
            st.markdown(f"`{i}. [{prefix}] {t['tool']}` ? `{t['input']}`")
