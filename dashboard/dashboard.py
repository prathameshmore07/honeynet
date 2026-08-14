"""
HoneyNet AI Adaptive Honeypot - Live Threat Intelligence Dashboard
Built with Streamlit & streamlit-autorefresh for real-time forensic monitoring.
"""
import json
import time
from datetime import datetime
from pathlib import Path
import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# Import backend modules safely
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.db import (
    init_db,
    get_all_sessions,
    get_events_by_session,
    get_all_events,
    get_overview_metrics,
    record_event
)
from backend.classifier import check_ollama_health, classify_command, generate_attacker_summary
from backend.mitre_mapper import map_command_to_mitre
from backend.asset_manager import get_assets_for_category, scan_template_files
from backend.config import TEMPLATES_DIR, COWRIE_LOG_PATH

# Streamlit Page Setup
st.set_page_config(
    page_title="HoneyNet | AI Adaptive Honeypot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema if not present
init_db()

# Custom CSS for Premium Dark Cybersecurity UI
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Headers */
    h1, h2, h3, h4 {
        color: #f8fafc;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #151d2f;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetricValue"] {
        color: #38bdf8;
        font-size: 1.8rem;
        font-weight: 800;
    }
    
    /* Category Badges */
    .badge-finance {
        background-color: #064e3b;
        color: #34d399;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        border: 1px solid #059669;
    }
    .badge-git {
        background-color: #451a03;
        color: #fbbf24;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        border: 1px solid #d97706;
    }
    .badge-aws {
        background-color: #0c4a6e;
        color: #38bdf8;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        border: 1px solid #0284c7;
    }
    .badge-hr {
        background-color: #4c0519;
        color: #fb7185;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        border: 1px solid #e11d48;
    }
    .badge-other {
        background-color: #1e293b;
        color: #94a3b8;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        border: 1px solid #334155;
    }
    
    /* Summary Card */
    .ai-summary-card {
        background: linear-gradient(135deg, #131b2e 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 12px 0 20px 0;
    }
    
    /* Code/Terminal style */
    .term-box {
        background-color: #030712;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 12px 16px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.88rem;
        color: #10b981;
        overflow-x: auto;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR & CONTROLS -----------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=64)
    st.title("HoneyNet Control")
    st.caption("AI-Powered Adaptive Honeypot v1.0")
    
    # Auto-refresh interval toggle
    auto_refresh = st.checkbox("Live Auto-Refresh (2s)", value=True)
    if auto_refresh:
        # Refresh every 2000 ms
        st_autorefresh(interval=2000, key="honeynet_autorefresh")
        
    if st.button("🔄 Refresh Data Now", use_container_width=True):
        st.rerun()

    st.markdown("---")
    st.subheader("System Health")
    
    # Check Ollama status
    ollama_ok, ollama_msg = check_ollama_health()
    if ollama_ok and "running with model" in ollama_msg:
        st.success(f"🟢 **AI Engine:** Online ({ollama_msg.split('with model')[1].strip()})")
    elif ollama_ok:
        st.warning(f"🟡 **AI Engine:** Standby (Model loading / Heuristic ready)")
    else:
        st.info("🔵 **AI Engine:** Heuristic Fallback Active")
        
    # Check Cowrie log stream
    if COWRIE_LOG_PATH.exists() and COWRIE_LOG_PATH.stat().st_size > 0:
        st.success(f"🟢 **Honeypot Telemetry:** Active Stream ({COWRIE_LOG_PATH.stat().st_size // 1024} KB)")
    else:
        st.warning("🟡 **Honeypot Telemetry:** Awaiting connection")
        
    st.markdown("---")
    st.subheader("Interactive Attack Injector")
    st.write("Simulate an attacker command directly:")
    
    sim_session = st.selectbox("Target Session", ["sim_finance_01", "sim_git_02", "sim_aws_03", "sim_hr_04", "custom_session"])
    sim_cmd = st.text_input("Execute Command", value="cat /home/phil/finance/Payroll_2026_Confidential.csv")
    
    if st.button("⚡ Inject Attacker Command", use_container_width=True, type="primary"):
        cat, method = classify_command(sim_cmd)
        files = get_assets_for_category(cat) if cat != "other" else []
        tag, name, score = map_command_to_mitre(sim_cmd, cat)
        record_event(
            session_id=sim_session,
            src_ip="203.0.113.77",
            command=sim_cmd,
            category=cat,
            files_served=files,
            mitre_tag=tag,
            mitre_name=name,
            event_risk_score=score
        )
        st.toast(f"Injected: '{sim_cmd}' -> Classified as [{cat.upper()}]", icon="🎯")
        time.sleep(0.3)
        st.rerun()

    st.markdown("---")
    st.caption("ℹ️ **Honesty Note**: Files are pre-staged realistic synthetic assets; the AI model dynamically detects intent and triggers context-tailored asset deployments.")

# ----------------- MAIN DASHBOARD -----------------
# Header
col_title, col_status = st.columns([3, 1])
with col_title:
    st.title("🛡️ HoneyNet Threat Intelligence")
    st.markdown("Real-time behavioral telemetry, AI intent classification, and adaptive asset surface tracking.")
with col_status:
    st.markdown(f"<div style='text-align: right; padding-top: 15px; color: #64748b;'>Last Updated:<br><b>{datetime.now().strftime('%H:%M:%S')} UTC</b></div>", unsafe_allow_html=True)

# Fetch Data
metrics = get_overview_metrics()
sessions = get_all_sessions()
events = get_all_events(limit=150)

# Top KPIs
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric(label="Tracked Sessions", value=metrics.get("total_sessions", 0))
with kpi2:
    st.metric(label="Captured Commands", value=metrics.get("total_events", 0))
with kpi3:
    st.metric(label="Synthetic Assets Deployed", value=metrics.get("total_assets_served", 0))
with kpi4:
    max_risk = max([s["risk_score"] for s in sessions], default=0) if sessions else 0
    st.metric(label="Peak Threat Risk", value=f"{max_risk}/100")

st.markdown("---")

# Main Content Tabs
tab_live, tab_session, tab_forensics = st.tabs([
    "📡 Live Intercept Stream",
    "🕵️ Attacker Session Inspector",
    "📂 Synthetic Asset Vault"
])

# ----------------- TAB 1: LIVE INTERCEPT STREAM -----------------
with tab_live:
    st.subheader("Real-Time Attacker Command Telemetry")
    
    if not events:
        st.info("No attacker commands recorded yet. Use the sidebar to inject test commands or run `python3 honeypot_sim.py`.")
    else:
        # Prepare formatted table data
        rows = []
        for ev in events:
            cat = ev.get("category", "other")
            cat_badge = f"<span class='badge-{cat}'>{cat.upper()}</span>"
            
            files_list = []
            try:
                raw_files = ev.get("files_served", "[]")
                files_list = json.loads(raw_files) if isinstance(raw_files, str) else raw_files
            except Exception:
                files_list = []
                
            files_str = ", ".join(files_list[:2]) + (f" (+{len(files_list)-2} more)" if len(files_list) > 2 else "") if files_list else "—"
            
            ts = ev.get("timestamp", "")
            if "T" in ts:
                ts_formatted = ts.split("T")[1][:8]
            else:
                ts_formatted = ts[:8]
                
            mitre_str = f"<b>{ev.get('mitre_tag', 'T1059')}</b> {ev.get('mitre_name', '')}"
            
            rows.append({
                "Time": ts_formatted,
                "Session": f"<code>{ev.get('session_id', '')[:12]}</code>",
                "Attacker IP": ev.get("src_ip", "127.0.0.1"),
                "Command Executed": f"<code>{ev.get('command', '')}</code>",
                "Inferred Intent": cat_badge,
                "MITRE ATT&CK": mitre_str,
                "Assets Deployed": files_str,
                "Risk": f"<b>{ev.get('risk_score', 0)}</b>"
            })
            
        df = pd.DataFrame(rows)
        st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

# ----------------- TAB 2: SESSION INSPECTOR -----------------
with tab_session:
    if not sessions:
        st.info("No active sessions to inspect.")
    else:
        sess_options = {f"{s['session_id']} (IP: {s['src_ip']} | Cmds: {s['total_commands']} | Risk: {s['risk_score']})": s['session_id'] for s in sessions}
        selected_label = st.selectbox("Select Attacker Session:", list(sess_options.keys()))
        selected_sess_id = sess_options[selected_label]
        
        # Fetch session details
        sess_data = next((s for s in sessions if s["session_id"] == selected_sess_id), None)
        sess_events = get_events_by_session(selected_sess_id)
        
        if sess_data:
            # AI Attacker Summary Box
            summary = sess_data.get("ai_summary", "")
            if not summary and sess_events:
                cmds = [e["command"] for e in sess_events if e.get("command")]
                summary = generate_attacker_summary(cmds)
                
            st.markdown(f"""
            <div class="ai-summary-card">
                <div style="font-size: 0.8rem; text-transform: uppercase; color: #38bdf8; font-weight: 700; margin-bottom: 4px;">
                    🤖 AI Attacker Intent & Objective Assessment
                </div>
                <div style="font-size: 1.05rem; color: #f8fafc; font-weight: 500;">
                    {summary or "Attacker is currently performing initial discovery."}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Session Stats Row
            s_col1, s_col2, s_col3, s_col4 = st.columns(4)
            with s_col1:
                st.markdown(f"**Session ID:** `{sess_data['session_id']}`")
                st.markdown(f"**Source IP:** `{sess_data['src_ip']}`")
            with s_col2:
                st.markdown(f"**Total Commands:** {sess_data['total_commands']}")
                cats_raw = sess_data.get("categories_triggered", "[]")
                try:
                    cats_list = json.loads(cats_raw) if isinstance(cats_raw, str) else cats_raw
                except Exception:
                    cats_list = []
                st.markdown(f"**Targeted Assets:** {', '.join([c.upper() for c in cats_list]) if cats_list else 'Reconnaissance'}")
            with s_col3:
                risk_val = sess_data.get("risk_score", 0)
                st.markdown(f"**Calculated Threat Score:** {risk_val}/100")
                st.progress(min(1.0, risk_val / 100.0))
            with s_col4:
                st.markdown(f"**First Active:** {sess_data.get('start_time', '')[:19]}")
                st.markdown(f"**Last Seen:** {sess_data.get('last_active', '')[:19]}")
                
            # Chronological Command Timeline
            st.markdown("#### Command Execution Chronology")
            for i, ev in enumerate(sess_events, 1):
                cat = ev.get("category", "other")
                badge = f"<span class='badge-{cat}'>{cat.upper()}</span>"
                mitre = f"<code>{ev.get('mitre_tag', '')}</code> {ev.get('mitre_name', '')}"
                
                with st.expander(f"#{i} [{ev.get('timestamp', '')[:19]}] {ev.get('command', '')}  |  Intent: {cat.upper()}", expanded=(i == len(sess_events))):
                    c_left, c_right = st.columns([2, 1])
                    with c_left:
                        st.markdown(f"**Command:** `{ev.get('command', '')}`")
                        st.markdown(f"**MITRE ATT&CK Mapping:** {mitre}")
                        st.markdown(f"**Risk Contribution:** +{ev.get('risk_score', 0)} pts")
                    with c_right:
                        st.markdown(f"**Intent Classified:** {badge}", unsafe_allow_html=True)
                        files_str = ev.get("files_served", "[]")
                        try:
                            f_list = json.loads(files_str) if isinstance(files_str, str) else files_str
                        except Exception:
                            f_list = []
                        if f_list:
                            st.markdown(f"**Assets Revealed ({len(f_list)}):**")
                            for f_item in f_list:
                                st.markdown(f"- 📄 `{f_item}`")
                        else:
                            st.caption("No sensitive asset reveal triggered.")

# ----------------- TAB 3: ASSET VAULT FORENSICS -----------------
with tab_forensics:
    st.subheader("Pre-Staged Synthetic Asset Catalog")
    st.markdown("These realistic, synthetic assets are deployed to engage and track attackers across distinct intent paths.")
    
    cat_select = st.radio("Asset Category:", ["finance", "git", "aws", "hr"], horizontal=True)
    
    cat_dir = TEMPLATES_DIR / cat_select
    if cat_dir.exists():
        files_in_cat = scan_template_files(cat_select)
        st.markdown(f"**Found {len(files_in_cat)} synthetic assets in `{cat_select}/`:**")
        
        for f_name in files_in_cat:
            f_path = cat_dir / f_name
            with st.expander(f"📄 {f_name}", expanded=False):
                if f_path.is_file():
                    try:
                        content = f_path.read_text(encoding="utf-8", errors="ignore")
                        st.code(content, language="bash" if ".env" in f_name or "credentials" in f_name else "text")
                    except Exception as e:
                        st.error(f"Cannot preview file: {e}")
                else:
                    st.caption("Directory structure entry.")
    else:
        st.warning(f"Template directory `{cat_dir}` not found.")
