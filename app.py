import logging
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException, status, Request
from pydantic import BaseModel, Field

# --- CUSTOM IMPORTS ---
from models.predictor import get_predictor
from backend.autoscaler import AutoScaler

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api")

app = FastAPI(title="AutoScaling Predictor API", version="1.0.0", tags=["Logic/Backend"])

# --- Global State ---
# In a distributed system, this would be in Redis/Database.
# For this project, we keep it here to track 'last_scale_time'.
scaler = AutoScaler()

# --- Pydantic Models (Validation) ---

class DataPoint(BaseModel):
    timestamp: datetime
    requests: int = Field(..., ge=0, description="Number of requests")
    bytes: int = Field(..., ge=0, description="Data transfer size")

class PredictionRequest(BaseModel):
    historical_data: List[DataPoint]
    forecast_window: int = Field(5, ge=1, le=60, description="Minutes to forecast ahead")
    model_type: Literal["arima", "prophet", "lstm"]

class PredictionResult(BaseModel):
    timestamp: datetime
    predicted_load: float

class PredictionResponse(BaseModel):
    predictions: List[PredictionResult]
    model_name: str
    confidence: float

class ScalingRequest(BaseModel):
    predicted_load: float = Field(..., gt=0)
    current_servers: int = Field(..., ge=1)
    # last_scale_time is optional because the backend tracks it, 
    # but we allow the frontend to pass it if we were stateless.
    # For now, we rely on the global 'scaler' state.

class ScalingResponse(BaseModel):
    action: Literal["scale_up", "scale_down", "maintain"]
    target_servers: int
    estimated_cost_per_hour: float
    reason: str

class MetricsResponse(BaseModel):
    model_accuracy: dict
    current_load: float
    running_servers: int
    cost_24h: float

# --- Middleware ---

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response Status: {response.status_code}")
    return response

# --- Endpoints ---

@app.post("/predict", response_model=PredictionResponse, tags=["AI Modeling"])
async def predict_load(payload: PredictionRequest):
    """
    Accepts historical data and returns future load predictions.
    Used by M2 (Modeler) logic.
    """
    try:
        # Factory pattern to get the right model
        predictor = get_predictor(payload.model_type)
        
        # Convert Pydantic models to list of dicts for the predictor
        history_data = [d.model_dump(mode='json') for d in payload.historical_data]
        
        predictions = predictor.predict(history_data, payload.forecast_window)
        
        return {
            "predictions": predictions,
            "model_name": predictor.get_model_name(),
            "confidence": 0.85  # Mock confidence for now
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Prediction failed")

@app.post("/recommend-scaling", response_model=ScalingResponse, tags=["Scaling Logic"])
async def recommend_scaling(payload: ScalingRequest):
    """
    Logic rule engine (M3) to decide whether to scale up or down.
    Uses the advanced 'AutoScaler' class with cooldowns.
    """
    logger.info(f"Checking scaling for load: {payload.predicted_load} with {payload.current_servers} servers.")
    
    # Delegate logic to our robust AutoScaler class
    decision = scaler.decide_scaling_action(
        current_servers=payload.current_servers, 
        predicted_load=payload.predicted_load
    )
    
    return {
        "action": decision["action"],
        "target_servers": decision["target_servers"],
        "estimated_cost_per_hour": scaler.calculate_cost(decision["target_servers"]),
        "reason": decision["reason"]
    }

@app.get("/metrics", response_model=MetricsResponse, tags=["Monitoring"])
async def get_metrics():
    """
    Returns system health and model performance metrics.
    """
    # In a real app, these would come from a database or monitoring tool (Prometheus)
    return {
        "model_accuracy": {
            "rmse": 12.5,
            "mae": 8.2,
            "mape": 0.05
        },
        "current_load": 450.0,
        "running_servers": 2,
        "cost_24h": 21.60
    }

@app.post("/simulate", tags=["Simulation"])
async def run_simulation(data: List[DataPoint]):
    """
    P4 Deliverable: Run a simulation to calculate cost savings.
    Compare Static vs AutoScaling.
    """
    # Create a fresh scaler for isolation
    sim_scaler = AutoScaler()
    
    # 1. Sort data
    sorted_data = sorted(data, key=lambda x: x.timestamp)
    
    total_static_cost = 0.0
    total_auto_cost = 0.0
    
    STATIC_SERVER_COUNT = 10 # Baseline assumption
    current_auto_servers = 2 # Start small
    
    # Iterate through data (assuming 1-minute intervals)
    for point in sorted_data:
        # Cost accumulation (Cost per minute = Cost per hour / 60)
        cost_per_min = sim_scaler.cost_per_server_hour / 60.0
        
        total_static_cost += STATIC_SERVER_COUNT * cost_per_min
        total_auto_cost += current_auto_servers * cost_per_min
        
        # Make decision for NEXT minute
        # We assume 'requests' is the load
        decision = sim_scaler.decide_scaling_action(
            current_servers=current_auto_servers,
            predicted_load=point.requests,
            current_time=point.timestamp
        )
        current_auto_servers = decision["target_servers"]

    return {
        "static_cost": round(total_static_cost, 2),
        "auto_scaling_cost": round(total_auto_cost, 2),
        "savings": round(total_static_cost - total_auto_cost, 2),
        "savings_percentage": round(((total_static_cost - total_auto_cost) / total_static_cost) * 100, 2)
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
