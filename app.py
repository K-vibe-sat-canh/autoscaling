import logging
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException, status, Request
from pydantic import BaseModel, Field

from models.predictor import get_predictor

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api")

app = FastAPI(title="AutoScaling Predictor API", version="1.0.0")

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
    last_scale_time: datetime

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

@app.post("/predict", response_model=PredictionResponse)
async def predict_load(payload: PredictionRequest):
    """
    Accepts historical data and returns future load predictions.
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

@app.post("/recommend-scaling", response_model=ScalingResponse)
async def recommend_scaling(payload: ScalingRequest):
    """
    Logic rule engine to decide whether to scale up or down.
    """
    # Simple Logic Rule (Beginner friendly)
    # Assume 1 server handles 1000 requests/min comfortably
    MAX_CAPACITY_PER_SERVER = 1000
    COST_PER_SERVER = 0.45 
    
    # Calculate utilization
    total_capacity = payload.current_servers * MAX_CAPACITY_PER_SERVER
    utilization = payload.predicted_load / total_capacity if total_capacity > 0 else 1.0
    
    action = "maintain"
    target_servers = payload.current_servers
    reason = "Load is stable within operational limits."

    # Scaling Logic
    if utilization > 0.85:
        action = "scale_up"
        target_servers += 1
        reason = f"Predicted load ({payload.predicted_load}) exceeds 85% of capacity."
    elif utilization < 0.30 and payload.current_servers > 1:
        action = "scale_down"
        target_servers -= 1
        reason = f"Predicted load ({payload.predicted_load}) is below 30% of capacity."

    return {
        "action": action,
        "target_servers": target_servers,
        "estimated_cost_per_hour": target_servers * COST_PER_SERVER,
        "reason": reason
    }

@app.get("/metrics", response_model=MetricsResponse)
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

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
