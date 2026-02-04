"""
================================================================================
FILE: dashboard/main.py
PURPOSE: Main entry point for the Streamlit Dashboard UI
OWNER: M3 (Logic/Backend) & M4 (Frontend)
================================================================================
...
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import os

from utils.data_handler import (
    fetch_current_metrics,
    fetch_predictions,
    fetch_scaling_recommendation,
    fetch_simulation_results,
    fetch_cost_report,
    fetch_forecast,
    setup_auto_refresh
)

API_URL = "http://localhost:8000"
DEFAULT_FORECAST_WINDOW = 15
DEFAULT_REFRESH_RATE = 10
DATA_FILE_PATH = "data/clean_data.csv" # Path to generated data

COLORS = {
    "primary": "#1f77b4",
    "success": "#2ecc71",
    "danger": "#e74c3c",
    "warning": "#f39c12",
    "neutral": "#95a5a6",
    "background": "#0e1117",
    "card_bg": "#1a1a2e",
    "text": "#ffffff"
}

st.set_page_config(
    page_title="AutoScaling Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0e1117 0%, #1a1a2e 100%); }
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(31, 119, 180, 0.3);
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #0e1117 100%);
        border-right: 1px solid #2d3748;
    }
    .stButton > button {
        background: linear-gradient(135deg, #1f77b4 0%, #2ecc71 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 20px rgba(46, 204, 113, 0.4);
    }
    h1 {
        background: linear-gradient(90deg, #1f77b4, #2ecc71);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    .scale-card {
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    .scale-up { background: linear-gradient(135deg, rgba(231, 76, 60, 0.2) 0%, rgba(192, 57, 43, 0.3) 100%); border: 2px solid #e74c3c; }
    .scale-down { background: linear-gradient(135deg, rgba(46, 204, 113, 0.2) 0%, rgba(39, 174, 96, 0.3) 100%); border: 2px solid #2ecc71; }
    .maintain { background: linear-gradient(135deg, rgba(149, 165, 166, 0.2) 0%, rgba(127, 140, 141, 0.3) 100%); border: 2px solid #95a5a6; }
    .status-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; animation: pulse 2s infinite; }
    .status-online { background: #2ecc71; }
    .status-warning { background: #f39c12; }
    .status-critical { background: #e74c3c; }
    @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.7; transform: scale(1.1); } }
    hr { border: 0; height: 1px; background: linear-gradient(90deg, transparent, #2d3748, transparent); margin: 30px 0; }
</style>
""", unsafe_allow_html=True)

col_title, col_status = st.columns([4, 1])
with col_title:
    st.markdown("# 🚀 AutoScaling Command Center")
    st.markdown("*Real-time traffic prediction and intelligent server scaling*")
with col_status:
    try:
        metrics = fetch_current_metrics(API_URL)
        if metrics:
            st.markdown("""
                <div style="text-align: right; padding: 10px;">
                    <span class="status-dot status-online"></span>
                    <span style="color: #2ecc71; font-weight: 600;">ONLINE</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""<div style="text-align: right; padding: 10px;"><span class="status-dot status-warning"></span><span style="color: #f39c12; font-weight: 600;">DEGRADED</span></div>""", unsafe_allow_html=True)
    except Exception:
        st.markdown("""<div style="text-align: right; padding: 10px;"><span class="status-dot status-critical"></span><span style="color: #e74c3c; font-weight: 600;">OFFLINE</span></div>""", unsafe_allow_html=True)
        metrics = None

st.divider()

with st.sidebar:
    st.markdown("<div style='text-align: center; padding: 20px 0;'><h2 style='color: #1f77b4;'>⚙️ Control Panel</h2></div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("### 🤖 AI Model")
    model_type = st.selectbox("Select Prediction Model", options=["arima", "prophet", "lstm"], format_func=lambda x: {"arima": "📈 ARIMA (Fast)", "prophet": "🔮 Prophet (Robust)", "lstm": "🧠 LSTM (Deep)"}.get(x, x))
    st.divider()
    st.markdown("### ⏱️ Forecast Settings")
    forecast_window = st.slider("Prediction Window", 5, 60, DEFAULT_FORECAST_WINDOW, 5)
    time_granularity = st.radio("Time Granularity", ["1m", "5m", "15m"], horizontal=True)
    st.divider()
    st.markdown("### 🔄 Auto-Refresh")
    if st.toggle("Enable Auto-Refresh"):
        refresh_rate = st.number_input("Refresh Interval (s)", 5, 60, DEFAULT_REFRESH_RATE)
        st.session_state.auto_refresh = True
        setup_auto_refresh(refresh_rate)
    else:
        st.session_state.auto_refresh = False
    st.divider()
    st.markdown("### 💰 Cost Settings")
    static_server_count = st.number_input("Static Baseline Servers", 1, 50, 10)

st.markdown("## 📊 System Overview")
if metrics:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        load = metrics.get('current_load', 0)
        status = "🟢" if load < 500 else "🟡" if load < 1000 else "🔴"
        st.metric(f"{status} Current Load", f"{load:,.0f}", delta="req/min")
    with col2: st.metric("🖥️ Active Servers", f"{metrics['running_servers']}")
    with col3: st.metric("💵 24h Cost", f"${metrics['cost_24h']:,.2f}")
    with col4:
        acc = metrics.get('model_accuracy', {})
        st.metric("🎯 Model RMSE", f"{acc.get('rmse', 'N/A')}", delta=f"MAPE: {acc.get('mape', 0)*100:.1f}%")
else:
    st.error("⚠️ Backend Offline. Run 'uvicorn app:app --reload'")

st.divider()
st.markdown("## 📈 Load Prediction")
col_btn, col_info = st.columns([1, 3])
with col_btn: predict_clicked = st.button("🔮 Generate Prediction", use_container_width=True)
with col_info: st.markdown(f"<div style='padding: 10px; background: #1a1a2e; border-radius: 8px;'>Model: {model_type.upper()} | Window: {forecast_window} min</div>", unsafe_allow_html=True)

if predict_clicked or st.session_state.get('auto_refresh', False):
    with st.spinner("🔄 Fetching predictions..."):
        prediction_data = fetch_predictions(API_URL, forecast_window, model_type)
    
    if prediction_data and 'predictions' in prediction_data:
        preds = prediction_data['predictions']
        df_pred = pd.DataFrame(preds)
        df_pred['timestamp'] = pd.to_datetime(df_pred['timestamp'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_pred['timestamp'], y=df_pred['predicted_load'], mode='lines+markers', name='Predicted Load', line=dict(color=COLORS['primary'], width=3), fill='tozeroy', fillcolor='rgba(31, 119, 180, 0.2)'))
        
        if metrics:
            cap = metrics['running_servers'] * 1000
            fig.add_hline(y=cap * 0.85, line_dash="dash", line_color=COLORS['danger'], annotation_text="Scale Up (85%)")
            fig.add_hline(y=cap * 0.30, line_dash="dash", line_color=COLORS['success'], annotation_text="Scale Down (30%)")
            
        fig.update_layout(title="Load Forecast", template="plotly_dark", height=400, margin=dict(l=20, r=20, t=40, b=20), hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("⚡ Scaling Recommendation")
        max_load = df_pred['predicted_load'].max()
        curr_servers = metrics['running_servers'] if metrics else 1
        recommendation = fetch_scaling_recommendation(API_URL, max_load, curr_servers)
        
        if recommendation:
            act = recommendation['action']
            style = "scale-up" if act == "scale_up" else "scale-down" if act == "scale_down" else "maintain"
            icon = "⬆️" if act == "scale_up" else "⬇️" if act == "scale_down" else "➡️"
            st.markdown(f"""
                <div class="scale-card {style}">
                    <h1>{icon}</h1><h2>{act.upper().replace('_', ' ')}</h2>
                    <p style="color:#b0b0b0">{recommendation['reason']}</p>
                    <hr>
                    <div style="display:flex; justify-content:space-around">
                        <div><p>Target Servers</p><h3>{recommendation['target_servers']}</h3></div>
                        <div><p>Est Cost</p><h3>${recommendation['estimated_cost_per_hour']:.2f}</h3></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

st.divider()
st.markdown("## 💰 Cost Analysis & Savings Report")
st.markdown("**ĐIỂM CỘNG**: So sánh chi phí Static Deployment vs AutoScaling với giả định unit cost.")

col_hours, col_btn = st.columns([2, 1])
with col_hours:
    sim_hours = st.slider("Simulation Duration (hours)", 1, 168, 24, help="Chọn số giờ để mô phỏng chi phí")
with col_btn:
    run_cost_report = st.button("📊 Generate Cost Report", use_container_width=True)

if run_cost_report:
    with st.spinner("🧮 Calculating costs using real NASA traffic data..."):
        cost_report = fetch_cost_report(API_URL, sim_hours)
    
    if cost_report:
        # Cost comparison cards
        col_static, col_auto, col_save = st.columns(3)
        
        static_info = cost_report['cost_comparison']['static_deployment']
        auto_info = cost_report['cost_comparison']['auto_scaling']
        savings_info = cost_report['savings']
        
        with col_static:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #331414 0%, #4a1a1a 100%); 
                            padding: 25px; border-radius: 15px; border: 2px solid #e74c3c; text-align: center;
                            box-shadow: 0 8px 32px rgba(231, 76, 60, 0.3);'>
                    <h4 style='color: #e74c3c; margin: 0;'>❌ Static Deployment</h4>
                    <h1 style='color: #ff6b6b; margin: 10px 0;'>{static_info['total_cost']}</h1>
                    <p style='color: #999; margin: 0;'>{static_info['servers']} servers cố định</p>
                    <p style='color: #666; font-size: 12px;'>{static_info['cost_per_hour']}/hour</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col_auto:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #143322 0%, #1a4a2e 100%); 
                            padding: 25px; border-radius: 15px; border: 2px solid #2ecc71; text-align: center;
                            box-shadow: 0 8px 32px rgba(46, 204, 113, 0.3);'>
                    <h4 style='color: #2ecc71; margin: 0;'>✅ AutoScaling</h4>
                    <h1 style='color: #6bff9a; margin: 10px 0;'>{auto_info['total_cost']}</h1>
                    <p style='color: #999; margin: 0;'>Avg: {auto_info['avg_servers']} servers</p>
                    <p style='color: #666; font-size: 12px;'>Dynamic allocation</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col_save:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #142233 0%, #1a3352 100%); 
                            padding: 25px; border-radius: 15px; border: 2px solid #3498db; text-align: center;
                            box-shadow: 0 8px 32px rgba(52, 152, 219, 0.3);'>
                    <h4 style='color: #3498db; margin: 0;'>💵 TIẾT KIỆM</h4>
                    <h1 style='color: #5dade2; margin: 10px 0;'>{savings_info['amount']}</h1>
                    <p style='color: #2ecc71; font-weight: bold; margin: 0;'>{savings_info['percentage']}</p>
                    <p style='color: #f39c12; font-size: 14px;'>📅 Monthly: {savings_info['monthly_projection']}</p>
                </div>
            """, unsafe_allow_html=True)
        
        # Conclusion box
        st.markdown(f"""
            <div style='background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
                        padding: 20px; border-radius: 10px; border-left: 4px solid #f39c12; margin-top: 20px;'>
                <h4 style='color: #f39c12; margin: 0 0 10px 0;'>📋 Kết Luận</h4>
                <p style='color: #ddd; margin: 0;'>{cost_report['conclusion']}</p>
                <p style='color: #888; margin-top: 10px; font-size: 12px;'>
                    📊 Data points analyzed: {cost_report['data_points_used']} | 
                    🔄 Scaling events: {cost_report['scaling_events']}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Show scaling events history
        if cost_report.get('scaling_history') and len(cost_report['scaling_history']) > 0:
            with st.expander(f"📜 View Scaling Events History ({cost_report['scaling_events']} total)"):
                events_df = pd.DataFrame(cost_report['scaling_history'])
                st.dataframe(events_df, use_container_width=True)

st.divider()
st.markdown("## 🧪 Legacy Cost Simulation")
st.markdown("Compare Static deployment vs AutoScaling using **Real Data** generated by M1.")

if st.button("🧪 Run Cost Simulation with REAL DATA", use_container_width=True):
    if not os.path.exists(DATA_FILE_PATH):
        st.error(f"❌ Data file not found at {DATA_FILE_PATH}. Please run 'python src/data_pipeline.py' first.")
    else:
        with st.spinner("Loading data and calculating costs... This may take a moment."):
            # Load real data
            df_sim = pd.read_csv(DATA_FILE_PATH)
            # Sample first 2000 rows (~33 hours) for speed in demo
            df_sample = df_sim.head(2000)
            traffic_payload = df_sample.to_dict(orient="records")
            
            sim_results = fetch_simulation_results(API_URL, traffic_payload)
            
        if sim_results:
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.markdown(f"<div style='background:#331414; padding:20px; border-radius:10px; border:1px solid #e74c3c; text-align:center'><h2 style='color:#e74c3c'>${sim_results['static_cost']:.2f}</h2><p>Static Cost (10 servers)</p></div>", unsafe_allow_html=True)
            with col_s2:
                st.markdown(f"<div style='background:#143322; padding:20px; border-radius:10px; border:1px solid #2ecc71; text-align:center'><h2 style='color:#2ecc71'>${sim_results['auto_scaling_cost']:.2f}</h2><p>AutoScaling Cost</p></div>", unsafe_allow_html=True)
            with col_s3:
                st.markdown(f"<div style='background:#142233; padding:20px; border-radius:10px; border:1px solid #1f77b4; text-align:center'><h2 style='color:#1f77b4'>${sim_results['savings']:.2f}</h2><p>TOTAL SAVED ({sim_results['savings_percentage']}%)</p></div>", unsafe_allow_html=True)
            
            st.success(f"Simulation completed using {len(df_sample)} data points from 'clean_data.csv'.")

st.divider()
st.markdown("<div style='text-align: center; color: #666;'>AutoScaling Predictor v2.0 - Full Integrated System</div>", unsafe_allow_html=True)
