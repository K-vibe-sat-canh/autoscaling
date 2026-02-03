import logging
import datetime
from typing import List, Literal, Optional

# FastAPI: The framework that creates the Web Server.
# HTTPException: To send errors (like 404 Not Found).
from fastapi import FastAPI, HTTPException, status, Request

# Pydantic: Ensures the data we receive (JSON) matches the shapes we expect.
from pydantic import BaseModel, Field

# --- CUSTOM IMPORTS (Our code) ---
# We import the factory function to get our AI model.
from models.predictor import get_predictor
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

# ==============================================================================
# 3. GLOBAL STATE
# In a real big app, we'd use a Database (Postgres) or Cache (Redis).
# For this project, we store the 'scaler' in memory. 
# It remembers 'last_scale_time' to enforce cooldowns.
# ==============================================================================
scaler = AutoScaler()

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

# ==============================================================================
# 7. RUN SERVER
# If you run `python app.py`, this starts the server.
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
