import streamlit as st
import pandas as pd
import time
from utils.data_handler import (
    fetch_current_metrics, 
    fetch_predictions, 
    fetch_scaling_recommendation,
    setup_auto_refresh
)

# Configuration
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Auto-Scaling Dashboard", layout="wide")

st.title("⚡ Auto-Scaling Prediction Dashboard")

# --- Sidebar Controls ---
st.sidebar.header("Configuration")
model_type = st.sidebar.selectbox("Select Model", ["arima", "prophet", "lstm"])
forecast_window = st.sidebar.slider("Forecast Window (minutes)", 5, 60, 15)
refresh_rate = st.sidebar.number_input("Refresh Rate (seconds)", 5, 60, 10)
st.session_state.auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh", value=False)

setup_auto_refresh(refresh_rate)

# --- 1. System Overview Metrics ---
st.subheader("System Overview")
metrics = fetch_current_metrics(API_URL)

if metrics:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Load", f"{metrics['current_load']} req/min")
    col2.metric("Active Servers", f"{metrics['running_servers']}")
    col3.metric("24h Cost", f"${metrics['cost_24h']}")
    col4.metric("Model RMSE", f"{metrics['model_accuracy']['rmse']}")
else:
    st.warning("Could not load metrics.")

st.divider()

# --- 2. Predictions ---
st.subheader(f"Load Forecast ({model_type.upper()})")

if st.button("Generate Prediction") or st.session_state.auto_refresh:
    data = fetch_predictions(API_URL, forecast_window, model_type)
    
    if data:
        preds = data['predictions']
        df_pred = pd.DataFrame(preds)
        df_pred['timestamp'] = pd.to_datetime(df_pred['timestamp'])
        
        # Display Chart
        st.line_chart(df_pred.set_index('timestamp')['predicted_load'])
        
        # --- 3. Scaling Recommendation ---
        # Get the highest predicted load in the window to be safe
        max_predicted_load = df_pred['predicted_load'].max()
        current_servers = metrics['running_servers'] if metrics else 1
        
        rec = fetch_scaling_recommendation(API_URL, max_predicted_load, current_servers)
        
        if rec:
            st.subheader("Scaling Recommendation")
            
            # Color code the action
            color = "blue"
            if rec['action'] == "scale_up":
                color = "red"
            elif rec['action'] == "scale_down":
                color = "green"
                
            st.markdown(f"""
            <div style="padding: 20px; border-radius: 10px; border: 2px solid {color}; text-align: center;">
                <h2 style="color: {color};">{rec['action'].upper().replace('_', ' ')}</h2>
                <p><strong>Target Servers:</strong> {rec['target_servers']}</p>
                <p><strong>Reason:</strong> {rec['reason']}</p>
                <p><strong>Est. Hourly Cost:</strong> ${rec['estimated_cost_per_hour']}</p>
            </div>
            """, unsafe_allow_html=True)
            
    else:
        st.info("Waiting for prediction data...")
