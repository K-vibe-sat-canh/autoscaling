# 🤝 Team Handoff Guide - Dashboard, Backend & Frontend Integration

> **For:** M1 (Data), M2 (Modeler), M4 (Frontend)  
> **From:** M3 (Logic/Backend)  
> **Purpose:** Quick reference so you can integrate your work with mine.

---

## 🏗️ System Overview (30 seconds)

```
[M4: Dashboard]  ──HTTP──►  [M3: Backend API]  ──calls──►  [M2: AI Models]
   Streamlit                   FastAPI                      ARIMA/LSTM
   Port 8501                   Port 8000                    
```

**Key Point:** The Dashboard does NOT calculate scaling logic. It just displays what the Backend returns.

---

## 📂 Who Owns What?

| Folder/File | Owner | What it does |
|-------------|-------|--------------|
| `app.py` | M3 | Main API server (FastAPI) |
| `backend/autoscaler.py` | M3 | Scaling decision logic |
| `models/predictor.py` | M2 | Load/run AI models |
| `dashboard/main.py` | M4 | Streamlit UI |
| `dashboard/utils/` | M3/M4 | API client functions |
| `saved_models/` | M2 | Trained model files (.pkl, .h5) |
| `data/` | M1 | Clean CSV files |

---

## 🔌 API Endpoints (What M4/Frontend Needs to Know)

### 1. `GET /health`
**Use:** Check if backend is running.
```json
Response: {"status": "ok", "timestamp": "..."}
```

### 2. `GET /metrics`
**Use:** Get current system stats for dashboard cards.
```json
Response: {
  "current_load": 450.0,
  "running_servers": 2,
  "cost_24h": 21.60,
  "model_accuracy": {"rmse": 12.5, "mae": 8.2, "mape": 0.05}
}
```

### 3. `POST /predict`
**Use:** Get AI predictions for future load.
```json
Request: {
  "historical_data": [{"timestamp": "2026-01-27T10:00:00", "requests": 100, "bytes": 1024}],
  "forecast_window": 15,
  "model_type": "arima"  // Options: "arima", "prophet", "lstm"
}

Response: {
  "predictions": [{"timestamp": "...", "predicted_load": 123.45}, ...],
  "model_name": "ARIMA",
  "confidence": 0.85
}
```

### 4. `POST /recommend-scaling`
**Use:** Get scaling decision (scale up/down/maintain).
```json
Request: {
  "predicted_load": 2500,
  "current_servers": 2
}

Response: {
  "action": "scale_up",  // Options: "scale_up", "scale_down", "maintain"
  "target_servers": 3,
  "estimated_cost_per_hour": 1.35,
  "reason": "High Load! Predicted 2500 reqs exceeds 85% of 2 servers."
}
```

### 5. `POST /simulate`
**Use:** Calculate cost savings (Static vs AutoScaling).
```json
Request: [
  {"timestamp": "2026-01-27T00:00:00", "requests": 100, "bytes": 512},
  {"timestamp": "2026-01-27T00:01:00", "requests": 150, "bytes": 768},
  ...
]

Response: {
  "static_cost": 108.00,
  "auto_scaling_cost": 45.20,
  "savings": 62.80,
  "savings_percentage": 58.15
}
```

---

## 🤖 For M2 (Modeler): How to Integrate Your Models

### Step 1: Save your trained model
```python
# Example for ARIMA
import joblib
joblib.dump(your_model, "saved_models/arima_model.pkl")
```

### Step 2: Update `models/predictor.py`
In the `ARIMAPredictor.predict()` method, replace the mock logic:
```python
def predict(self, historical_data, steps_ahead):
    # YOUR REAL PREDICTION CODE HERE
    # Use self.model.forecast(steps_ahead)
    pass
```

### Step 3: Test it
```powershell
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"historical_data": [...], "forecast_window": 5, "model_type": "arima"}'
```

---

## 🖥️ For M4 (Frontend): How to Connect Dashboard

### The data_handler.py is ready!
I've already created helper functions in `dashboard/utils/data_handler.py`:

| Function | Calls | Returns |
|----------|-------|---------|
| `fetch_current_metrics(api_url)` | `GET /metrics` | dict of metrics |
| `fetch_predictions(api_url, window, model)` | `POST /predict` | predictions list |
| `fetch_scaling_recommendation(api_url, load, servers)` | `POST /recommend-scaling` | scaling decision |

### Just import and use:
```python
from utils.data_handler import fetch_current_metrics, fetch_predictions

metrics = fetch_current_metrics("http://localhost:8000")
print(metrics['current_load'])
```

---

## 📊 For M1 (Data): What CSV Format I Need

Your clean data should have these columns:

| Column | Type | Example |
|--------|------|---------|
| `timestamp` | ISO datetime string | `2026-01-27T10:00:00` |
| `requests` | int (>= 0) | `1500` |
| `bytes` | int (>= 0) | `2048` |

**Example CSV:**
```csv
timestamp,requests,bytes
2026-01-27T10:00:00,1500,2048
2026-01-27T10:01:00,1600,2100
2026-01-27T10:02:00,1450,1980
```

---

## ⚡ Quick Start Commands

```powershell
# Terminal 1: Start Backend
cd d:\Downloads\dataflow\prj\autoscaling-predictor
.\.venv\Scripts\Activate.ps1
uvicorn app:app --reload

# Terminal 2: Start Dashboard
cd d:\Downloads\dataflow\prj\autoscaling-predictor
.\.venv\Scripts\Activate.ps1
streamlit run dashboard/main.py
```

---

## ⚠️ Common Integration Issues

| Problem | Who Fixes | Solution |
|---------|-----------|----------|
| Dashboard can't connect | M3/M4 | Make sure Backend is running on port 8000 |
| Prediction returns random data | M2 | Model files not loaded (check `saved_models/`) |
| `/simulate` returns 0 savings | M1 | Check if CSV has correct columns |
| "422 Unprocessable Entity" | Everyone | JSON format doesn't match expected schema |

---

## 📞 Contact Points

- **Scaling logic bugs** → Ask M3
- **AI prediction bugs** → Ask M2
- **Dashboard UI bugs** → Ask M4
- **Data format issues** → Ask M1

---

> **Last Updated:** 2026-01-27
