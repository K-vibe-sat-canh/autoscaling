import requests
import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import logging

# Setup basic logging for the dashboard
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard")

def fetch_current_metrics(api_url):
    """
    GET /metrics from backend.
    Includes retry logic for connection errors.
    """
    endpoint = f"{api_url}/metrics"
    retries = 3
    
    for i in range(retries):
        try:
            response = requests.get(endpoint, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {i+1} failed: {e}")
            if i == retries - 1:
                st.error(f"Failed to fetch metrics after {retries} attempts. Is the backend running?")
                return None
            time.sleep(1)

@st.cache_data(ttl=60)
def fetch_predictions(api_url, forecast_window, model_type):
    """
    POST /predict to backend.
    Uses Streamlit caching to prevent re-fetching on every UI interaction.
    """
    endpoint = f"{api_url}/predict"
    
    # Generate mock historical data to send to the API (since we don't have a real DB yet)
    # beginner tip: In a real app, you'd fetch this from a database first.
    now = datetime.utcnow()
    mock_history = []
    for i in range(30): # Last 30 minutes
        t = now - timedelta(minutes=30-i)
        mock_history.append({
            "timestamp": t.isoformat(),
            "requests": int(300 + (i * 5) + (i % 5 * 10)), # Fake pattern
            "bytes": 1024 * i
        })

    payload = {
        "historical_data": mock_history,
        "forecast_window": forecast_window,
        "model_type": model_type
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Prediction API Error: {e}")
        return None

def fetch_scaling_recommendation(api_url, predicted_load, current_servers):
    """
    POST /recommend-scaling
    """
    endpoint = f"{api_url}/recommend-scaling"
    
    payload = {
        "predicted_load": predicted_load,
        "current_servers": current_servers,
        "last_scale_time": datetime.utcnow().isoformat()
    }
    
    try:
        response = requests.post(endpoint, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Scaling API Error: {e}")
        return None

def setup_auto_refresh(interval_seconds):
    """
    Manages auto-refresh state.
    """
    if 'last_updated' not in st.session_state:
        st.session_state.last_updated = time.time()
    
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False

    # Check if time to refresh
    now = time.time()
    if st.session_state.auto_refresh:
        if now - st.session_state.last_updated > interval_seconds:
            st.session_state.last_updated = now
            st.rerun()

    diff = int(now - st.session_state.last_updated)
    st.sidebar.markdown(f"**Last updated:** {diff} seconds ago")
