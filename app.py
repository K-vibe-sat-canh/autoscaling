import logging
import datetime
import json
import os
from typing import List, Literal, Optional

import pandas as pd
import numpy as np

# FastAPI: The framework that creates the Web Server.
# HTTPException: To send errors (like 404 Not Found).
from fastapi import FastAPI, HTTPException, status, Request, Query
from fastapi.middleware.cors import CORSMiddleware

# Pydantic: Ensures the data we receive (JSON) matches the shapes we expect.
from pydantic import BaseModel, Field

# --- CUSTOM IMPORTS (Our code) ---
# We import the factory function to get our AI model.
from models.predictor import get_predictor, XGBoostPredictor
# We import the AutoScaler class (the logic brain).
from backend.autoscaler import AutoScaler

# ==============================================================================
# 1. SETUP LOGGING
# Purpose: To see what's happening in the console when the server runs.
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api")

# ==============================================================================
# 2. CREATE APP
# This is the main application object.
# ==============================================================================
app = FastAPI(
    title="AutoScaling Predictor API", 
    version="2.0.0", 
    tags=["Logic/Backend"],
    description="API for prediction handling and autoscaling decisions."
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# 3. GLOBAL STATE
# In a real big app, we'd use a Database (Postgres) or Cache (Redis).
# For this project, we store the 'scaler' in memory. 
# It remembers 'last_scale_time' to enforce cooldowns.
# ==============================================================================
scaler = AutoScaler()

# Load XGBoost models globally for faster inference
xgb_predictor = XGBoostPredictor()

# Load traffic data for forecasting
DATA_PATH = "processed_data/nasa_traffic_15m.csv"
traffic_df = None
if os.path.exists(DATA_PATH):
    traffic_df = pd.read_csv(DATA_PATH, parse_dates=['timestamp'])

# ==============================================================================
# 4. DATA MODELS (Pydantic)
# These classes define the "Shape" of data we accept and return.
# ==============================================================================

class DataPoint(BaseModel):
    """Represents one row of traffic data (from CSV or Realtime)."""
    timestamp: datetime.datetime
    requests: int = Field(..., ge=0, description="Number of requests")
    bytes: int = Field(..., ge=0, description="Data transfer size")

class PredictionRequest(BaseModel):
    """What the Frontend sends to ask for a prediction."""
    historical_data: List[DataPoint]
    forecast_window: int = Field(5, ge=1, le=60, description="Minutes to forecast")
    model_type: Literal["arima", "prophet", "lstm"]

class PredictionResult(BaseModel):
    """One single prediction point."""
    timestamp: str 
    predicted_load: float

class PredictionResponse(BaseModel):
    """What we send back to the Frontend."""
    predictions: List[PredictionResult]
    model_name: str
    confidence: float

class ScalingRequest(BaseModel):
    """Frontend sends this to ask 'Should I scale?'"""
    predicted_load: float = Field(..., gt=0)
    current_servers: int = Field(..., ge=1)

class ScalingResponse(BaseModel):
    """The decision we send back."""
    action: Literal["scale_up", "scale_down", "maintain"]
    target_servers: int
    estimated_cost_per_hour: float
    reason: str

class MetricsResponse(BaseModel):
    """General health metrics."""
    model_accuracy: dict
    current_load: float
    running_servers: int
    cost_24h: float

# ==============================================================================
# 5. MIDDLEWARE
# Run this code for EVERY request (logging, timing, security, etc.)
# ==============================================================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response Status: {response.status_code}")
    return response

# ==============================================================================
# 6. API ENDPOINTS
# These are the URLs that our API exposes.
# ==============================================================================

# =============================================================================
# ENDPOINT: GET /forecast (REQUIRED BY COMPETITION)
# =============================================================================
@app.get("/forecast", tags=["AI Modeling"])
async def forecast_load(
    timestamp: str = Query(..., description="ISO timestamp or 'now' for current time"),
    steps: int = Query(4, ge=1, le=96, description="Number of 15-min intervals to forecast")
):
    """
    📈 FORECAST ENDPOINT (GET /forecast)
    
    Đây là endpoint chính theo yêu cầu đề bài.
    Nhận timestamp và trả về dự báo tải cho các khoảng thời gian tiếp theo.
    
    Parameters:
    - timestamp: Thời điểm bắt đầu dự báo (ISO format hoặc 'now')
    - steps: Số khoảng 15 phút cần dự báo (mặc định 4 = 1 giờ)
    
    Returns:
    - Danh sách predictions với timestamp và predicted_requests, predicted_bytes
    """
    try:
        # Parse timestamp
        if timestamp.lower() == 'now':
            base_time = datetime.datetime.now()
        else:
            base_time = pd.to_datetime(timestamp)
        
        # Use XGBoost model for prediction
        predictions = xgb_predictor.forecast(base_time, steps)
        
        return {
            "status": "success",
            "model": "XGBoost",
            "base_timestamp": base_time.isoformat(),
            "forecast_horizon": f"{steps * 15} minutes ({steps} intervals)",
            "predictions": predictions,
            "metrics": {
                "model_rmse": 43.13,  # From training
                "model_mape": "25.83%"
            }
        }
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast failed: {str(e)}"
        )


# =============================================================================
# ENDPOINT: GET /recommend-scaling (REQUIRED BY COMPETITION)
# =============================================================================
@app.get("/recommend-scaling", tags=["Scaling Logic"])
async def get_scaling_recommendation(
    predicted_requests: float = Query(..., gt=0, description="Predicted requests per 15 min"),
    current_servers: int = Query(1, ge=1, description="Current number of servers")
):
    """
    ⚖️ SCALING RECOMMENDATION (GET /recommend-scaling)
    
    Đây là endpoint theo yêu cầu đề bài.
    Nhận predicted_hits và trả về khuyến nghị scaling.
    
    Parameters:
    - predicted_requests: Số requests dự báo
    - current_servers: Số server hiện tại
    
    Returns:
    - action: SCALE_UP, SCALE_DOWN, hoặc MAINTAIN
    - target_servers: Số server khuyến nghị
    - cost_estimate: Chi phí ước tính
    """
    decision = scaler.decide_scaling_action(
        current_servers=current_servers,
        predicted_load=predicted_requests
    )
    
    # Calculate costs
    hourly_cost = scaler.calculate_cost(decision["target_servers"], 1)
    daily_cost = scaler.calculate_cost(decision["target_servers"], 24)
    monthly_cost = scaler.calculate_cost(decision["target_servers"], 24 * 30)
    
    return {
        "action": decision["action"].upper().replace("_", " "),
        "target_servers": decision["target_servers"],
        "current_servers": current_servers,
        "predicted_load": predicted_requests,
        "reason": decision["reason"],
        "cost_estimate": {
            "hourly": f"${hourly_cost:.2f}",
            "daily": f"${daily_cost:.2f}",
            "monthly": f"${monthly_cost:.2f}"
        },
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.post("/predict", response_model=PredictionResponse, tags=["AI Modeling"])
async def predict_load(payload: PredictionRequest):
    """
    ENDPOINT: POST /predict
    PURPOSE:  Predict future traffic based on history.
    ROLE:     M2 (Modeler) Integration.
    """
    try:
        # 1. Get the correct AI model (ARIMA, etc.)
        predictor = get_predictor(payload.model_type)
        
        # 2. Convert incoming data to simple list of dicts
        history_data = [d.model_dump(mode='json') for d in payload.historical_data]
        
        # 3. Run the prediction logic
        predictions = predictor.predict(history_data, payload.forecast_window)
        
        # 4. Return results
        return {
            "predictions": predictions,
            "model_name": predictor.get_model_name(),
            "confidence": 0.85  # Placeholder confidence
        }
    except ValueError as ve:
        # User asked for a model we don't have
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Prediction failed")

@app.post("/recommend-scaling", response_model=ScalingResponse, tags=["Scaling Logic"])
async def recommend_scaling(payload: ScalingRequest):
    """
    ENDPOINT: POST /recommend-scaling
    PURPOSE:  Decide server count.
    ROLE:     M3 (Logic) Core.
    """
    logger.info(f"Checking scaling for load: {payload.predicted_load} with {payload.current_servers} servers.")
    
    # 1. Ask the AutoScaler class (the Brain) for a decision
    decision = scaler.decide_scaling_action(
        current_servers=payload.current_servers, 
        predicted_load=payload.predicted_load
    )
    
    # 2. Return the decision
    return {
        "action": decision["action"],
        "target_servers": decision["target_servers"],
        "estimated_cost_per_hour": scaler.calculate_cost(decision["target_servers"]),
        "reason": decision["reason"]
    }

@app.get("/metrics", response_model=MetricsResponse, tags=["Monitoring"])
async def get_metrics():
    """
    ENDPOINT: GET /metrics
    PURPOSE:  Show system health on Dashboard.
    """
    # In a real app, this data comes from live monitoring.
    # Here, we hardcode representative values for the demo.
    return {
        "model_accuracy": {
            "rmse": 475.7,  # From our recent training run
            "mae": 350.2,
            "mape": 0.14
        },
        "current_load": 1250.0,
        "running_servers": 2,
        "cost_24h": 21.60
    }

@app.post("/simulate", tags=["Simulation"])
async def run_simulation(data: List[DataPoint]):
    """
    ENDPOINT: POST /simulate
    PURPOSE:  Calculate how much money we save!
    ROLE:     P4 Deliverable.
    """
    # 1. Create a NEW isolated scaler (so we don't mess up the live one)
    sim_scaler = AutoScaler()
    
    # 2. Sort data by time
    sorted_data = sorted(data, key=lambda x: x.timestamp)
    
    total_static_cost = 0.0
    total_auto_cost = 0.0
    
    STATIC_SERVER_COUNT = 10  # Baseline: What if we did nothing?
    current_auto_servers = 2  # Start small
    
    # 3. Loop through every minute of data
    for point in sorted_data:
        # Cost math: ($0.45 / 60 minutes) * count
        cost_per_min = sim_scaler.cost_per_server_hour / 60.0
        
        # Add costs
        total_static_cost += STATIC_SERVER_COUNT * cost_per_min
        total_auto_cost += current_auto_servers * cost_per_min
        
        # Make decision for NEXT minute based on this minute's load
        decision = sim_scaler.decide_scaling_action(
            current_servers=current_auto_servers,
            predicted_load=point.requests,
            current_time=point.timestamp
        )
        current_auto_servers = decision["target_servers"]

    # 4. Return comparison
    return {
        "static_cost": round(total_static_cost, 2),
        "auto_scaling_cost": round(total_auto_cost, 2),
        "savings": round(total_static_cost - total_auto_cost, 2),
        "savings_percentage": round(((total_static_cost - total_auto_cost) / total_static_cost) * 100, 2)
    }

@app.get("/health")
async def health_check():
    """Simple check to see if API is running."""
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}


# =============================================================================
# ENDPOINT: GET /cost-report (BONUS - ĐIỂM CỘNG)
# =============================================================================
@app.get("/cost-report", tags=["Cost Analysis"])
async def get_cost_report(
    simulation_hours: int = Query(24, ge=1, le=720, description="Hours to simulate")
):
    """
    💰 COST REPORT ENDPOINT (Điểm cộng)
    
    So sánh chi phí giữa Static Scaling và AutoScaling.
    Giúp giám khảo thấy được giá trị kinh tế của giải pháp.
    """
    if traffic_df is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Traffic data not found. Please run data pipeline first."
        )
    
    try:
        # Get subset of data for simulation
        intervals_needed = simulation_hours * 4  # 4 intervals per hour (15-min each)
        sim_data = traffic_df.head(min(intervals_needed, len(traffic_df))).copy()
        
        # Ensure timestamp is datetime and timezone-naive for comparison
        sim_data['timestamp'] = pd.to_datetime(sim_data['timestamp']).dt.tz_localize(None)
        
        # Static scaling cost (fixed 10 servers)
        STATIC_SERVERS = 10
        static_cost = STATIC_SERVERS * scaler.cost_per_server_hour * simulation_hours
        
        # AutoScaling simulation  
        sim_scaler = AutoScaler()  # Fresh scaler to avoid cooldown issues
        current_servers = 2
        total_auto_cost = 0.0
        scaling_events = []
        
        for idx, row in sim_data.iterrows():
            # Cost for this 15-min interval
            interval_cost = current_servers * scaler.cost_per_server_hour / 4
            total_auto_cost += interval_cost
            
            # Get scaling decision with timezone-naive datetime
            current_time = pd.to_datetime(row['timestamp'])
            if current_time.tzinfo is not None:
                current_time = current_time.replace(tzinfo=None)
                
            decision = sim_scaler.decide_scaling_action(
                current_servers=current_servers,
                predicted_load=row['request_count'],
                current_time=current_time
            )
            
            if decision['action'] != 'maintain':
                scaling_events.append({
                    "timestamp": str(row['timestamp']),
                    "action": decision['action'],
                    "from_servers": current_servers,
                    "to_servers": decision['target_servers'],
                    "load": float(row['request_count'])
                })
            
            current_servers = decision['target_servers']
        
        savings = static_cost - total_auto_cost
        savings_percent = (savings / static_cost) * 100 if static_cost > 0 else 0
        
        return {
            "simulation_period": f"{simulation_hours} hours",
            "data_points_used": len(sim_data),
            "cost_comparison": {
                "static_deployment": {
                    "servers": STATIC_SERVERS,
                    "total_cost": f"${static_cost:.2f}",
                    "cost_per_hour": f"${STATIC_SERVERS * scaler.cost_per_server_hour:.2f}"
                },
                "auto_scaling": {
                    "total_cost": f"${total_auto_cost:.2f}",
                    "avg_servers": f"{total_auto_cost / (scaler.cost_per_server_hour * simulation_hours):.1f}" if simulation_hours > 0 else "0"
                }
            },
            "savings": {
                "amount": f"${savings:.2f}",
                "percentage": f"{savings_percent:.1f}%",
                "monthly_projection": f"${savings * 30:.2f}"
            },
            "scaling_events": len(scaling_events),
            "scaling_history": scaling_events[:20],  # Show first 20 events
            "conclusion": f"AutoScaling tiết kiệm ${savings:.2f} ({savings_percent:.1f}%) trong {simulation_hours} giờ. Dự kiến tiết kiệm ${savings * 30:.2f}/tháng."
        }
    except Exception as e:
        logger.error(f"Cost report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cost calculation failed: {str(e)}"
        )


# ==============================================================================
# 7. RUN SERVER
# If you run `python app.py`, this starts the server.
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
