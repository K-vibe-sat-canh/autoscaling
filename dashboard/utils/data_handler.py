"""
================================================================================
FILE: dashboard/utils/data_handler.py
PURPOSE: API Client - Functions to communicate with the Backend API
OWNER: M3 (Logic/Backend)
================================================================================

This file contains helper functions that the Dashboard uses to communicate
with the FastAPI backend. Each function corresponds to one API endpoint.

ARCHITECTURE:
    Dashboard (main.py) ──uses──> data_handler.py ──HTTP──> Backend (app.py)

WHY SEPARATE FILE?
    1. Clean Code: Keep UI logic separate from API logic
    2. Reusability: These functions can be used by other scripts too
    3. Testing: Easy to mock these functions for unit tests
    4. Maintainability: If API changes, only update this file

DEPENDENCIES:
    - requests: HTTP client library (pip install requests)
    - streamlit: For error display and session state

ERROR HANDLING:
    - All functions use try/except to catch network errors
    - Returns None on failure (caller must check for None)
    - Errors are displayed using st.error() for user visibility
================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import requests      # HTTP client for making API calls
import streamlit as st  # For displaying errors and managing state
import time          # For sleep() in auto-refresh

# =============================================================================
# CONFIGURATION
# =============================================================================
# Timeout for API requests (in seconds)
# If the backend doesn't respond in this time, we abort and show an error
REQUEST_TIMEOUT = 5


# =============================================================================
# HELPER FUNCTION: Auto-Refresh
# =============================================================================
def setup_auto_refresh(interval_seconds: int) -> None:
    """
    Enables automatic page refresh at specified intervals.
    
    HOW IT WORKS:
        Streamlit doesn't have native auto-refresh, so we:
        1. Check if auto_refresh is enabled in session state
        2. If yes, sleep for the interval then trigger a rerun
        
    ARGUMENTS:
        interval_seconds (int): How many seconds to wait between refreshes.
                                Should be between 5 and 60.
    
    RETURNS:
        None
    
    USAGE:
        # In sidebar:
        if st.checkbox("Enable Auto-Refresh"):
            st.session_state.auto_refresh = True
            setup_auto_refresh(10)  # Refresh every 10 seconds
    
    WARNING:
        This function will cause the entire script to re-run.
        Any stateful widgets (like inputs) may reset.
    """
    # Check if auto_refresh is enabled in session state
    # session_state persists across reruns
    if st.session_state.get('auto_refresh', False):
        # Wait for the specified interval
        time.sleep(interval_seconds)
        # Trigger a full page rerun
        # This is a Streamlit-specific function
        st.rerun()


# =============================================================================
# API FUNCTION: GET /metrics
# =============================================================================
def fetch_current_metrics(api_url: str) -> dict | None:
    """
    Fetches current system metrics from the backend.
    
    API ENDPOINT:
        GET {api_url}/metrics
    
    WHAT IT RETURNS:
        A dictionary containing:
        {
            "current_load": 450.0,       # Current requests per minute
            "running_servers": 2,         # Number of active servers
            "cost_24h": 21.60,            # Cost in last 24 hours ($)
            "model_accuracy": {
                "rmse": 12.5,             # Root Mean Square Error
                "mae": 8.2,               # Mean Absolute Error
                "mape": 0.05              # Mean Absolute Percentage Error (0.05 = 5%)
            }
        }
    
    ARGUMENTS:
        api_url (str): Base URL of the backend API (e.g., "http://localhost:8000")
    
    RETURNS:
        dict: The metrics data if successful
        None: If the request fails (network error, server down, etc.)
    
    USAGE:
        metrics = fetch_current_metrics("http://localhost:8000")
        if metrics:
            print(f"Current load: {metrics['current_load']}")
        else:
            print("Backend is offline!")
    
    ERROR HANDLING:
        - Catches requests.exceptions.ConnectionError (server down)
        - Catches requests.exceptions.Timeout (server too slow)
        - Catches any other RequestException (generic HTTP error)
    """
    try:
        # Make the GET request to /metrics endpoint
        # timeout=REQUEST_TIMEOUT means we wait max 5 seconds
        response = requests.get(
            f"{api_url}/metrics", 
            timeout=REQUEST_TIMEOUT
        )
        
        # Check if the response was successful (HTTP 200 OK)
        if response.status_code == 200:
            # Parse JSON response into Python dictionary
            return response.json()
        else:
            # Server returned an error (4xx or 5xx)
            st.error(f"❌ API Error: /metrics returned {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        # Server is not reachable (not running, wrong port, etc.)
        st.error("🔌 Cannot connect to Backend. Is it running?")
        return None
        
    except requests.exceptions.Timeout:
        # Server took too long to respond
        st.error("⏱️ Backend request timed out. Server may be overloaded.")
        return None
        
    except requests.exceptions.RequestException as e:
        # Any other HTTP-related error
        st.error(f"❌ Network error: {e}")
        return None


# =============================================================================
# API FUNCTION: POST /predict
# =============================================================================
def fetch_predictions(api_url: str, forecast_window: int, model_type: str) -> dict | None:
    """
    Fetches load predictions from the AI model.
    
    API ENDPOINT:
        POST {api_url}/predict
    
    REQUEST BODY:
        {
            "historical_data": [
                {"timestamp": "2026-01-27T10:00:00", "requests": 1500, "bytes": 2048}
            ],
            "forecast_window": 15,  # Minutes to predict ahead
            "model_type": "arima"   # Model to use: "arima", "prophet", or "lstm"
        }
    
    WHAT IT RETURNS:
        {
            "predictions": [
                {"timestamp": "2026-01-27T10:01:00", "predicted_load": 1520.5},
                {"timestamp": "2026-01-27T10:02:00", "predicted_load": 1550.0},
                ...
            ],
            "model_name": "ARIMA (AutoRegressive Integrated Moving Average)",
            "confidence": 0.85
        }
    
    ARGUMENTS:
        api_url (str): Base URL of the backend API
        forecast_window (int): How many minutes ahead to predict (1-60)
        model_type (str): Which AI model to use ("arima", "prophet", "lstm")
    
    RETURNS:
        dict: Prediction data if successful
        None: If request fails
    
    USAGE:
        data = fetch_predictions("http://localhost:8000", 15, "arima")
        if data:
            for pred in data['predictions']:
                print(f"{pred['timestamp']}: {pred['predicted_load']}")
    
    NOTE:
        Currently uses mock historical data for demo purposes.
        In production, you would pass real data from the database or CSV.
    """
    # --- PREPARE REQUEST BODY ---
    # In a real app, you would fetch actual historical data from a database
    # For this demo, we use mock data so the API doesn't crash
    
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
        # Make the POST request with JSON body
        response = requests.post(
            f"{api_url}/predict",
            json=payload,  # 'json=' automatically sets Content-Type header
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            # API returned an error
            # Common error: 422 Unprocessable Entity (schema validation failed)
            st.error(f"❌ Prediction API Error: {response.status_code}")
            # Show the actual error message from the API
            try:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"Details: {error_detail}")
            except:
                pass
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to Backend for predictions.")
        return None
        
    except requests.exceptions.Timeout:
        st.error("⏱️ Prediction request timed out.")
        return None
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Prediction network error: {e}")
        return None


# =============================================================================
# API FUNCTION: POST /recommend-scaling
# =============================================================================
def fetch_scaling_recommendation(api_url: str, predicted_load: float, current_servers: int) -> dict | None:
    """
    Gets a scaling recommendation from the AutoScaler logic.
    
    API ENDPOINT:
        POST {api_url}/recommend-scaling
    
    REQUEST BODY:
        {
            "predicted_load": 2500.0,  # Expected requests/minute
            "current_servers": 2       # Currently running servers
        }
    
    WHAT IT RETURNS:
        {
            "action": "scale_up",       # "scale_up", "scale_down", or "maintain"
            "target_servers": 3,        # Recommended number of servers
            "estimated_cost_per_hour": 1.35,  # Cost at target server count
            "reason": "High Load! Predicted 2500 reqs exceeds 85% of 2 servers."
        }
    
    THE LOGIC (in backend/autoscaler.py):
        - If utilization > 85%: SCALE UP
        - If utilization < 30% and servers > 1: SCALE DOWN
        - Otherwise: MAINTAIN
        - Cooldown: Must wait 5 minutes between scaling actions
    
    ARGUMENTS:
        api_url (str): Base URL of the backend API
        predicted_load (float): The predicted number of requests/minute
        current_servers (int): How many servers are currently running
    
    RETURNS:
        dict: Scaling recommendation if successful
        None: If request fails
    
    USAGE:
        rec = fetch_scaling_recommendation("http://localhost:8000", 2500, 2)
        if rec:
            if rec['action'] == 'scale_up':
                print(f"Need to add servers! Target: {rec['target_servers']}")
    """
    payload = {
        "predicted_load": predicted_load,
        "current_servers": current_servers
    }
    
    try:
        response = requests.post(
            f"{api_url}/recommend-scaling",
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Scaling API Error: {response.status_code}")
            try:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"Details: {error_detail}")
            except:
                pass
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to Backend for scaling recommendation.")
        return None
        
    except requests.exceptions.Timeout:
        st.error("⏱️ Scaling recommendation request timed out.")
        return None
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Scaling network error: {e}")
        return None


# =============================================================================
# API FUNCTION: POST /simulate
# =============================================================================
def fetch_simulation_results(api_url: str, traffic_data: list) -> dict | None:
    """
    Runs a cost simulation comparing Static vs AutoScaling deployment.
    
    API ENDPOINT:
        POST {api_url}/simulate
    
    REQUEST BODY:
        [
            {"timestamp": "2026-01-27T00:00:00", "requests": 100, "bytes": 512},
            {"timestamp": "2026-01-27T00:01:00", "requests": 150, "bytes": 768},
            ...
        ]
    
    WHAT IT RETURNS:
        {
            "static_cost": 108.00,        # Cost with 10 fixed servers for 24h
            "auto_scaling_cost": 45.20,   # Cost using our algorithm
            "savings": 62.80,             # Difference (money saved!)
            "savings_percentage": 58.15   # Percentage saved
        }
    
    HOW THE SIMULATION WORKS (in app.py):
        1. Loops through each data point (1 minute of traffic)
        2. For Static: Always charges for 10 servers
        3. For AutoScaling: Uses AutoScaler to decide server count
        4. Accumulates costs for both scenarios
        5. Returns the comparison
    
    ARGUMENTS:
        api_url (str): Base URL of the backend API
        traffic_data (list): List of traffic data points with timestamp, requests, bytes
    
    RETURNS:
        dict: Simulation results if successful
        None: If request fails
    
    USAGE:
        data = [
            {"timestamp": "2026-01-27T00:00:00", "requests": 100, "bytes": 512},
            {"timestamp": "2026-01-27T00:01:00", "requests": 200, "bytes": 1024},
        ]
        results = fetch_simulation_results("http://localhost:8000", data)
        if results:
            print(f"You saved ${results['savings']}!")
    """
    try:
        response = requests.post(
            f"{api_url}/simulate",
            json=traffic_data,
            timeout=30  # Longer timeout for simulation (processing heavy)
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Simulation API Error: {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to Backend for simulation.")
        return None
        
    except requests.exceptions.Timeout:
        st.error("⏱️ Simulation request timed out. Data may be too large.")
        return None
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Simulation network error: {e}")
        return None


# =============================================================================
# API FUNCTION: GET /cost-report (NEW - FOR BONUS POINTS)
# =============================================================================
def fetch_cost_report(api_url: str, simulation_hours: int = 24) -> dict | None:
    """
    Fetches cost comparison report between Static and AutoScaling.
    
    API ENDPOINT:
        GET {api_url}/cost-report?simulation_hours=24
    
    WHAT IT RETURNS:
        {
            "simulation_period": "24 hours",
            "cost_comparison": {
                "static_deployment": {"servers": 10, "total_cost": "$108.00"},
                "auto_scaling": {"total_cost": "$45.20", "avg_servers": "4.2"}
            },
            "savings": {
                "amount": "$62.80",
                "percentage": "58.1%",
                "monthly_projection": "$1884.00"
            },
            "conclusion": "AutoScaling tiết kiệm $62.80..."
        }
    
    ARGUMENTS:
        api_url (str): Base URL of the backend API
        simulation_hours (int): Number of hours to simulate (default 24)
    
    RETURNS:
        dict: Cost report if successful
        None: If request fails
    """
    try:
        response = requests.get(
            f"{api_url}/cost-report",
            params={"simulation_hours": simulation_hours},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Cost Report API Error: {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to Backend for cost report.")
        return None
        
    except requests.exceptions.Timeout:
        st.error("⏱️ Cost report request timed out.")
        return None
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Cost report network error: {e}")
        return None


# =============================================================================
# API FUNCTION: GET /forecast (NEW - COMPETITION REQUIRED)
# =============================================================================
def fetch_forecast(api_url: str, timestamp: str = "now", steps: int = 4) -> dict | None:
    """
    Fetches traffic forecast using XGBoost model.
    
    API ENDPOINT:
        GET {api_url}/forecast?timestamp=now&steps=4
    
    WHAT IT RETURNS:
        {
            "status": "success",
            "model": "XGBoost",
            "predictions": [
                {"timestamp": "...", "predicted_requests": 850, "predicted_bytes": 17000000},
                ...
            ]
        }
    
    ARGUMENTS:
        api_url (str): Base URL of the backend API
        timestamp (str): Starting timestamp or "now"
        steps (int): Number of 15-min intervals to forecast
    
    RETURNS:
        dict: Forecast data if successful
        None: If request fails
    """
    try:
        response = requests.get(
            f"{api_url}/forecast",
            params={"timestamp": timestamp, "steps": steps},
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Forecast API Error: {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to Backend for forecast.")
        return None
        
    except requests.exceptions.Timeout:
        st.error("⏱️ Forecast request timed out.")
        return None
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Forecast network error: {e}")
        return None


# =============================================================================
# TESTING (Only runs if this file is executed directly)
# =============================================================================
if __name__ == "__main__":
    """
    Quick test to verify API connectivity.
    Run this file directly to test: python data_handler.py
    """
    print("🧪 Testing API connections...")
    
    API_URL = "http://localhost:8000"
    
    # Test 1: Health Check
    print("\n1. Testing /metrics endpoint...")
    metrics = fetch_current_metrics(API_URL)
    if metrics:
        print(f"   ✅ Metrics: {metrics}")
    else:
        print("   ❌ Failed to fetch metrics")
    
    # Test 2: Predictions
    print("\n2. Testing /predict endpoint...")
    preds = fetch_predictions(API_URL, 5, "arima")
    if preds:
        print(f"   ✅ Got {len(preds.get('predictions', []))} predictions")
    else:
        print("   ❌ Failed to fetch predictions")
    
    # Test 3: Scaling
    print("\n3. Testing /recommend-scaling endpoint...")
    rec = fetch_scaling_recommendation(API_URL, 2500, 2)
    if rec:
        print(f"   ✅ Recommendation: {rec['action']}")
    else:
        print("   ❌ Failed to fetch recommendation")
    
    print("\n✅ All tests complete!")
