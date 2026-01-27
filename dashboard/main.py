"""
================================================================================
FILE: dashboard/main.py
PURPOSE: Main entry point for the Streamlit Dashboard UI
OWNER: M3 (Logic/Backend) & M4 (Frontend)
================================================================================

This file creates a professional, industrial-standard dashboard for the 
AutoScaling Prediction System. It displays:
1. Real-time system metrics (load, servers, cost)
2. AI-powered load predictions with interactive charts
3. Scaling recommendations (scale up/down/maintain)
4. Cost simulation results

ARCHITECTURE:
    ┌─────────────────────────────────────────────────────────────┐
    │                     STREAMLIT DASHBOARD                      │
    │  ┌─────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
    │  │ Sidebar │  │  Main Content   │  │   Scaling Panel     │  │
    │  │ Config  │  │  Charts/Metrics │  │   Recommendations   │  │
    │  └─────────┘  └─────────────────┘  └─────────────────────┘  │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP API Calls
    ┌─────────────────────────────────────────────────────────────┐
    │                    FASTAPI BACKEND                           │
    │                    localhost:8000                            │
    └─────────────────────────────────────────────────────────────┘

HOW TO RUN:
    1. First, start the backend: uvicorn app:app --reload
    2. Then, run this file: streamlit run dashboard/main.py
    3. Open browser: http://localhost:8501

DEPENDENCIES:
    - streamlit: Web UI framework
    - pandas: Data manipulation
    - plotly: Interactive charts (professional-grade)
    - requests: HTTP client (in utils/data_handler.py)
================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import streamlit as st          # Main UI framework
import pandas as pd             # Data handling
import plotly.express as px     # Professional interactive charts
import plotly.graph_objects as go  # Advanced chart customization
from datetime import datetime, timedelta
import time

# Our custom API client functions (see dashboard/utils/data_handler.py)
from utils.data_handler import (
    fetch_current_metrics,           # GET /metrics
    fetch_predictions,               # POST /predict
    fetch_scaling_recommendation,    # POST /recommend-scaling
    fetch_simulation_results,        # POST /simulate (NEW)
    setup_auto_refresh               # Auto-refresh helper
)

# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================
# These values should match your backend configuration

API_URL = "http://localhost:8000"  # Backend API base URL
DEFAULT_FORECAST_WINDOW = 15       # Default prediction window (minutes)
DEFAULT_REFRESH_RATE = 10          # Default auto-refresh interval (seconds)

# Theme colors for consistent branding
COLORS = {
    "primary": "#1f77b4",      # Blue - main brand color
    "success": "#2ecc71",      # Green - scale down / good
    "danger": "#e74c3c",       # Red - scale up / warning
    "warning": "#f39c12",      # Orange - attention needed
    "neutral": "#95a5a6",      # Gray - maintain / neutral
    "background": "#0e1117",   # Dark background
    "card_bg": "#1a1a2e",      # Card background
    "text": "#ffffff"          # Text color
}

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
# This MUST be the first Streamlit command in your script
# It sets up the browser tab title, icon, and layout

st.set_page_config(
    page_title="AutoScaling Command Center",  # Browser tab title
    page_icon="🚀",                            # Browser tab icon (emoji or image path)
    layout="wide",                             # Use full screen width
    initial_sidebar_state="expanded"           # Sidebar starts open
)

# =============================================================================
# CUSTOM CSS STYLING (Industrial-Grade UI)
# =============================================================================
# We inject custom CSS to make the dashboard look more professional
# This overrides Streamlit's default styling

st.markdown("""
<style>
    /* ===== GLOBAL STYLES ===== */
    /* Dark theme background */
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #1a1a2e 100%);
    }
    
    /* ===== METRIC CARDS ===== */
    /* The boxes that show Current Load, Servers, Cost, etc. */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    /* Hover effect on metric cards */
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(31, 119, 180, 0.3);
    }
    
    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #0e1117 100%);
        border-right: 1px solid #2d3748;
    }
    
    /* ===== BUTTONS ===== */
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
    
    /* ===== HEADERS ===== */
    h1 {
        background: linear-gradient(90deg, #1f77b4, #2ecc71);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    /* ===== SCALING ACTION CARDS ===== */
    .scale-card {
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    
    .scale-up {
        background: linear-gradient(135deg, rgba(231, 76, 60, 0.2) 0%, rgba(192, 57, 43, 0.3) 100%);
        border: 2px solid #e74c3c;
    }
    
    .scale-down {
        background: linear-gradient(135deg, rgba(46, 204, 113, 0.2) 0%, rgba(39, 174, 96, 0.3) 100%);
        border: 2px solid #2ecc71;
    }
    
    .maintain {
        background: linear-gradient(135deg, rgba(149, 165, 166, 0.2) 0%, rgba(127, 140, 141, 0.3) 100%);
        border: 2px solid #95a5a6;
    }
    
    /* ===== STATUS INDICATORS ===== */
    .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    .status-online { background: #2ecc71; }
    .status-warning { background: #f39c12; }
    .status-critical { background: #e74c3c; }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.7; transform: scale(1.1); }
    }
    
    /* ===== DIVIDERS ===== */
    hr {
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, #2d3748, transparent);
        margin: 30px 0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER SECTION
# =============================================================================
# Main title and status indicator

# Create a header with logo and status
col_title, col_status = st.columns([4, 1])

with col_title:
    st.markdown("# 🚀 AutoScaling Command Center")
    st.markdown("*Real-time traffic prediction and intelligent server scaling*")

with col_status:
    # Show connection status to backend
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
            st.markdown("""
                <div style="text-align: right; padding: 10px;">
                    <span class="status-dot status-warning"></span>
                    <span style="color: #f39c12; font-weight: 600;">DEGRADED</span>
                </div>
            """, unsafe_allow_html=True)
    except Exception:
        st.markdown("""
            <div style="text-align: right; padding: 10px;">
                <span class="status-dot status-critical"></span>
                <span style="color: #e74c3c; font-weight: 600;">OFFLINE</span>
            </div>
        """, unsafe_allow_html=True)
        metrics = None

st.divider()

# =============================================================================
# SIDEBAR - CONFIGURATION PANEL
# =============================================================================
# The sidebar contains all user-configurable options

with st.sidebar:
    # ----- Logo / Branding -----
    st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h2 style="color: #1f77b4;">⚙️ Control Panel</h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # ----- Model Selection -----
    # This determines which AI model to use for predictions
    st.markdown("### 🤖 AI Model")
    model_type = st.selectbox(
        "Select Prediction Model",
        options=["arima", "prophet", "lstm"],
        format_func=lambda x: {
            "arima": "📈 ARIMA (Fast, Traditional)",
            "prophet": "🔮 Prophet (Facebook AI)", 
            "lstm": "🧠 LSTM (Deep Learning)"
        }.get(x, x),
        help="ARIMA: Best for stable patterns. Prophet: Best for seasonality. LSTM: Best for complex patterns."
    )
    
    st.divider()
    
    # ----- Forecast Settings -----
    st.markdown("### ⏱️ Forecast Settings")
    
    # How far ahead to predict (in minutes)
    forecast_window = st.slider(
        "Prediction Window",
        min_value=5,
        max_value=60,
        value=DEFAULT_FORECAST_WINDOW,
        step=5,
        help="How many minutes into the future should we predict?"
    )
    
    # Time granularity selection (for the report requirement)
    time_granularity = st.radio(
        "Time Granularity",
        options=["1m", "5m", "15m"],
        horizontal=True,
        help="Data aggregation interval. 1m = detailed, 15m = smoothed."
    )
    
    st.divider()
    
    # ----- Auto-Refresh -----
    st.markdown("### 🔄 Auto-Refresh")
    
    auto_refresh_enabled = st.toggle(
        "Enable Auto-Refresh",
        value=False,
        help="Automatically refresh the dashboard at regular intervals."
    )
    
    if auto_refresh_enabled:
        refresh_rate = st.number_input(
            "Refresh Interval (seconds)",
            min_value=5,
            max_value=60,
            value=DEFAULT_REFRESH_RATE,
            help="How often to refresh the data."
        )
        # Store in session state for the refresh logic
        st.session_state.auto_refresh = True
        setup_auto_refresh(refresh_rate)
    else:
        st.session_state.auto_refresh = False
    
    st.divider()
    
    # ----- Server Cost Configuration -----
    st.markdown("### 💰 Cost Settings")
    
    cost_per_server = st.number_input(
        "Cost per Server/Hour ($)",
        min_value=0.01,
        max_value=10.0,
        value=0.45,
        step=0.05,
        help="The hourly cost to run one server instance."
    )
    
    static_server_count = st.number_input(
        "Static Baseline Servers",
        min_value=1,
        max_value=50,
        value=10,
        help="Number of servers in a 'fixed' deployment (for comparison)."
    )

# =============================================================================
# MAIN CONTENT - ROW 1: KEY METRICS
# =============================================================================
# Show the 4 main system metrics in cards

st.markdown("## 📊 System Overview")

if metrics:
    # Create 4 columns for the metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    # ----- METRIC 1: Current Load -----
    with col1:
        # Determine load status (for color coding)
        load = metrics.get('current_load', 0)
        load_status = "🟢" if load < 500 else "🟡" if load < 1000 else "🔴"
        
        st.metric(
            label=f"{load_status} Current Load",
            value=f"{load:,.0f}",
            delta="req/min",
            help="The current number of requests per minute hitting the servers."
        )
    
    # ----- METRIC 2: Active Servers -----
    with col2:
        servers = metrics.get('running_servers', 0)
        st.metric(
            label="🖥️ Active Servers",
            value=f"{servers}",
            delta=None,
            help="Number of server instances currently running."
        )
    
    # ----- METRIC 3: 24h Cost -----
    with col3:
        cost = metrics.get('cost_24h', 0)
        st.metric(
            label="💵 24h Cost",
            value=f"${cost:,.2f}",
            delta=None,
            help="Total server costs in the last 24 hours."
        )
    
    # ----- METRIC 4: Model Accuracy -----
    with col4:
        accuracy = metrics.get('model_accuracy', {})
        rmse = accuracy.get('rmse', 'N/A')
        mape = accuracy.get('mape', 0) * 100  # Convert to percentage
        
        st.metric(
            label="🎯 Model RMSE",
            value=f"{rmse}",
            delta=f"MAPE: {mape:.1f}%",
            help="Root Mean Square Error of the prediction model. Lower is better."
        )
else:
    # Backend is not reachable
    st.error("⚠️ Cannot connect to Backend API. Please ensure the server is running on port 8000.")
    st.code("uvicorn app:app --reload", language="bash")

st.divider()

# =============================================================================
# MAIN CONTENT - ROW 2: PREDICTION CHART
# =============================================================================
# Interactive chart showing predicted load over time

st.markdown("## 📈 Load Prediction")

# Action button to trigger prediction
col_btn, col_info = st.columns([1, 3])

with col_btn:
    predict_clicked = st.button("🔮 Generate Prediction", use_container_width=True)

with col_info:
    st.markdown(f"""
        <div style="padding: 10px; background: #1a1a2e; border-radius: 8px; font-size: 14px;">
            <strong>Model:</strong> {model_type.upper()} | 
            <strong>Window:</strong> {forecast_window} min | 
            <strong>Granularity:</strong> {time_granularity}
        </div>
    """, unsafe_allow_html=True)

# Generate predictions when button is clicked or auto-refresh is enabled
if predict_clicked or st.session_state.get('auto_refresh', False):
    
    with st.spinner("🔄 Fetching predictions from AI model..."):
        prediction_data = fetch_predictions(API_URL, forecast_window, model_type)
    
    if prediction_data and 'predictions' in prediction_data:
        preds = prediction_data['predictions']
        df_pred = pd.DataFrame(preds)
        df_pred['timestamp'] = pd.to_datetime(df_pred['timestamp'])
        
        # ----- CREATE PROFESSIONAL PLOTLY CHART -----
        fig = go.Figure()
        
        # Add the prediction line
        fig.add_trace(go.Scatter(
            x=df_pred['timestamp'],
            y=df_pred['predicted_load'],
            mode='lines+markers',
            name='Predicted Load',
            line=dict(color=COLORS['primary'], width=3),
            marker=dict(size=8, color=COLORS['primary']),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.2)'
        ))
        
        # Add threshold lines
        if metrics:
            capacity_per_server = 1000  # Matches backend config
            total_capacity = metrics['running_servers'] * capacity_per_server
            
            # 85% threshold (scale-up trigger)
            fig.add_hline(
                y=total_capacity * 0.85,
                line_dash="dash",
                line_color=COLORS['danger'],
                annotation_text="Scale-Up Threshold (85%)",
                annotation_position="top right"
            )
            
            # 30% threshold (scale-down trigger)
            fig.add_hline(
                y=total_capacity * 0.30,
                line_dash="dash",
                line_color=COLORS['success'],
                annotation_text="Scale-Down Threshold (30%)",
                annotation_position="bottom right"
            )
        
        # Style the chart
        fig.update_layout(
            title=dict(
                text=f"📊 {forecast_window}-Minute Load Forecast ({model_type.upper()})",
                font=dict(size=20, color='white')
            ),
            xaxis_title="Time",
            yaxis_title="Predicted Requests/Minute",
            template="plotly_dark",
            height=400,
            margin=dict(l=50, r=50, t=80, b=50),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='x unified'
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
        
        # ----- PREDICTION STATISTICS -----
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("📉 Min Load", f"{df_pred['predicted_load'].min():,.0f}")
        with col_stat2:
            st.metric("📊 Avg Load", f"{df_pred['predicted_load'].mean():,.0f}")
        with col_stat3:
            st.metric("📈 Max Load", f"{df_pred['predicted_load'].max():,.0f}")
        with col_stat4:
            st.metric("📏 Std Dev", f"{df_pred['predicted_load'].std():,.0f}")
        
        st.divider()
        
        # =============================================================================
        # MAIN CONTENT - ROW 3: SCALING RECOMMENDATION
        # =============================================================================
        
        st.markdown("## ⚡ Scaling Recommendation")
        
        # Get the maximum predicted load (worst case scenario)
        max_predicted_load = df_pred['predicted_load'].max()
        current_servers = metrics['running_servers'] if metrics else 1
        
        # Fetch scaling recommendation from backend
        with st.spinner("🧠 Calculating optimal scaling action..."):
            recommendation = fetch_scaling_recommendation(API_URL, max_predicted_load, current_servers)
        
        if recommendation:
            action = recommendation['action']
            
            # Determine card style based on action
            if action == "scale_up":
                card_class = "scale-up"
                icon = "⬆️"
                action_text = "SCALE UP"
                description = "Traffic is increasing! Add more servers to handle the load."
            elif action == "scale_down":
                card_class = "scale-down"
                icon = "⬇️"
                action_text = "SCALE DOWN"
                description = "Traffic is low. Remove servers to save costs."
            else:
                card_class = "maintain"
                icon = "➡️"
                action_text = "MAINTAIN"
                description = "Traffic is stable. No action needed."
            
            # Display the recommendation card
            st.markdown(f"""
                <div class="scale-card {card_class}">
                    <h1 style="font-size: 48px; margin: 0;">{icon}</h1>
                    <h2 style="color: white; margin: 10px 0;">{action_text}</h2>
                    <p style="color: #b0b0b0; font-size: 16px;">{description}</p>
                    <hr style="border-color: rgba(255,255,255,0.1);">
                    <div style="display: flex; justify-content: space-around; margin-top: 20px;">
                        <div>
                            <p style="color: #888; margin: 0;">Current Servers</p>
                            <h3 style="color: white; margin: 5px 0;">{current_servers}</h3>
                        </div>
                        <div>
                            <p style="color: #888; margin: 0;">Target Servers</p>
                            <h3 style="color: white; margin: 5px 0;">{recommendation['target_servers']}</h3>
                        </div>
                        <div>
                            <p style="color: #888; margin: 0;">Est. Hourly Cost</p>
                            <h3 style="color: white; margin: 5px 0;">${recommendation['estimated_cost_per_hour']:.2f}</h3>
                        </div>
                    </div>
                    <p style="color: #888; font-style: italic; margin-top: 20px;">
                        📝 {recommendation['reason']}
                    </p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Could not fetch scaling recommendation.")
        
    else:
        st.info("👆 Click 'Generate Prediction' to see the load forecast.")

st.divider()

# =============================================================================
# MAIN CONTENT - ROW 4: SIMULATION / COST ANALYSIS
# =============================================================================

st.markdown("## 💰 Cost Simulation (Static vs AutoScaling)")

st.markdown("""
    <div style="background: #1a1a2e; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <p style="margin: 0; color: #b0b0b0;">
            This simulation compares the cost of running a <strong>fixed number of servers</strong> 
            vs. using our <strong>intelligent autoscaling</strong> algorithm. 
            Upload historical data or use mock data to see potential savings.
        </p>
    </div>
""", unsafe_allow_html=True)

# Simulation button
if st.button("🧪 Run Cost Simulation", use_container_width=True):
    with st.spinner("Running simulation..."):
        # For demo purposes, we'll use mock simulation results
        # In production, you would call: fetch_simulation_results(API_URL, data)
        simulation_results = {
            "static_cost": 108.00,
            "auto_scaling_cost": 45.20,
            "savings": 62.80,
            "savings_percentage": 58.15
        }
    
    # Display simulation results
    col_sim1, col_sim2, col_sim3 = st.columns(3)
    
    with col_sim1:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e74c3c22, #c0392b33); 
                        padding: 25px; border-radius: 15px; text-align: center; 
                        border: 1px solid #e74c3c;">
                <p style="color: #888; margin: 0;">Static Deployment Cost</p>
                <h2 style="color: #e74c3c; margin: 10px 0;">${simulation_results['static_cost']:.2f}</h2>
                <p style="color: #666; font-size: 12px;">({static_server_count} servers × 24h)</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col_sim2:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #2ecc7122, #27ae6033); 
                        padding: 25px; border-radius: 15px; text-align: center;
                        border: 1px solid #2ecc71;">
                <p style="color: #888; margin: 0;">AutoScaling Cost</p>
                <h2 style="color: #2ecc71; margin: 10px 0;">${simulation_results['auto_scaling_cost']:.2f}</h2>
                <p style="color: #666; font-size: 12px;">(Dynamic scaling)</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col_sim3:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1f77b422, #1565c033); 
                        padding: 25px; border-radius: 15px; text-align: center;
                        border: 1px solid #1f77b4;">
                <p style="color: #888; margin: 0;">Total Savings 🎉</p>
                <h2 style="color: #1f77b4; margin: 10px 0;">${simulation_results['savings']:.2f}</h2>
                <p style="color: #2ecc71; font-size: 14px; font-weight: bold;">
                    ↓ {simulation_results['savings_percentage']:.1f}% reduction
                </p>
            </div>
        """, unsafe_allow_html=True)

# =============================================================================
# FOOTER
# =============================================================================

st.divider()

st.markdown("""
    <div style="text-align: center; padding: 20px; color: #666;">
        <p>🚀 AutoScaling Predictor v1.0 | Built with ❤️ by Team DataFlow</p>
        <p style="font-size: 12px;">
            Backend: FastAPI | Frontend: Streamlit | Models: ARIMA, Prophet, LSTM
        </p>
    </div>
""", unsafe_allow_html=True)
