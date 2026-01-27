import requests
import streamlit as st
import time

def setup_auto_refresh(interval_seconds):
    """
    Simulates auto-refresh by re-running the script.
    Note: Streamlit has native autorefresh in newer versions, 
    but this is a robust manual implementation.
    """
    if st.session_state.get('auto_refresh'):
        time.sleep(interval_seconds)
        st.rerun()

def fetch_current_metrics(api_url):
    """
    GET /metrics
    """
    try:
        response = requests.get(f"{api_url}/metrics", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to Backend: {e}")
    return None

def fetch_predictions(api_url, forecast_window, model_type):
    """
    POST /predict
    """
    # Create dummy historical data for the API (since we are just testing logic)
    # in a real app, you'd pull this from a database or the uploaded CSV
    payload = {
        "historical_data": [
            {
                "timestamp": "2026-01-27T10:00:00",
                "requests": 1500,
                "bytes": 2048
            }
        ],
        "forecast_window": forecast_window,
        "model_type": model_type
    }
    
    try:
        response = requests.post(f"{api_url}/predict", json=payload, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Prediction failed: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching predictions: {e}")
    return None

def fetch_scaling_recommendation(api_url, predicted_load, current_servers):
    """
    POST /recommend-scaling
    """
    payload = {
        "predicted_load": predicted_load,
        "current_servers": current_servers,
        "last_scale_time": "2026-01-27T10:00:00" # Dummy, backend handles real state
    }
    
    try:
        response = requests.post(f"{api_url}/recommend-scaling", json=payload, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Scaling recommendation failed: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching recommendation: {e}")
    return None
