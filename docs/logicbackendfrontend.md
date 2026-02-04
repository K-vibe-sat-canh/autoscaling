# 🧠 Complete Beginner's Guide to the AutoScaling Project

> **Purpose of this document:** This is YOUR personal reference. It explains EVERYTHING in this project so you can understand, make decisions, and fix bugs yourself. Read this carefully before debugging or making changes.

---

## 📁 Project File Structure (Click to Jump)

```
autoscaling-predictor/
├── app.py                  # 🔥 THE MAIN API (FastAPI) - Start here for Backend
├── requirements.txt        # 📦 Python dependencies
├── config.yaml             # ⚙️ Configuration settings
├── README.md               # 📖 Project overview for judges
│
├── backend/                # 🧠 LOGIC LAYER (Your work as M3)
│   ├── __init__.py         # Makes 'backend' a Python package
│   └── autoscaler.py       # ⭐ THE CORE LOGIC CLASS
│
├── models/                 # 🤖 AI MODEL LAYER (M2's work)
│   ├── __init__.py         # (may exist)
│   └── predictor.py        # Factory to load ARIMA/LSTM/Prophet
│
├── dashboard/              # 🖥️ FRONTEND LAYER (M4's work)
│   ├── main.py             # Streamlit app entry point
│   └── utils/
│       └── data_handler.py # Functions to call your API
│
└── saved_models/           # 💾 Where trained .pkl/.h5 models go (M2 creates)
```

---

## 🔗 Quick File Links (Click to Open)

| File | Purpose | Who Owns It |
|------|---------|-------------|
| [app.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/app.py) | Main API server with all endpoints | **YOU (M3)** |
| [backend/autoscaler.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/backend/autoscaler.py) | AutoScaler class with scaling logic | **YOU (M3)** |
| [backend/__init__.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/backend/__init__.py) | Makes `backend/` importable | **YOU (M3)** |
| [models/predictor.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/models/predictor.py) | AI model loading & prediction | M2 (Modeler) |
| [dashboard/main.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/dashboard/main.py) | Streamlit UI | M4 (Frontend) |
| [dashboard/utils/data_handler.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/dashboard/utils/data_handler.py) | API client functions for dashboard | **YOU (M3)** |
| [requirements.txt](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/requirements.txt) | Python package list | Everyone |
| [config.yaml](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/config.yaml) | Settings (thresholds, costs) | **YOU (M3)** |

---

## 🏗️ PART 1: Understanding the Architecture

### What is this project?
We are building an **AutoScaling System** that:
1. **Predicts** future traffic (requests per minute) using AI models.
2. **Decides** whether to add or remove servers based on that prediction.
3. **Saves money** by not running too many servers when traffic is low.

### The 3 Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 1: FRONTEND                        │
│  dashboard/main.py (Streamlit)                              │
│  - Shows charts, buttons, metrics                           │
│  - Calls the Backend API using HTTP requests                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ HTTP (localhost:8000)
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 2: BACKEND API                     │
│  app.py (FastAPI)                                           │
│  - Receives requests from Frontend                          │
│  - Calls the Logic layer (AutoScaler)                       │
│  - Calls the Model layer (predictor.py)                     │
│  - Returns JSON responses                                    │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌───────────────────────┐   ┌───────────────────────┐
│   LAYER 3a: LOGIC     │   │   LAYER 3b: AI MODELS │
│ backend/autoscaler.py │   │ models/predictor.py   │
│ - Scale up/down rules │   │ - ARIMA, Prophet, LSTM│
│ - Cooldown timer      │   │ - Returns predictions │
└───────────────────────┘   └───────────────────────┘
```

---

## 📚 PART 2: Core Concepts Explained

### 2.1 What is "Autoscaling"?

**Problem:** Imagine you run a website. 
- At 3 AM, only 10 users visit. You only need 1 server.
- At 8 PM, 10,000 users visit. You need 10 servers.

If you keep 10 servers running 24/7, you **waste money** at 3 AM.
If you only have 1 server, your site **crashes** at 8 PM.

**Solution:** Autoscaling = Automatically add/remove servers based on traffic.

### 2.2 What is "Utilization"?

**Formula:**
```
Utilization = (Actual Load) / (Total Capacity)
```

**Example:**
- You have **2 servers**. Each handles **1000 requests/min**.
- Total Capacity = 2 × 1000 = **2000 requests/min**.
- Current Load = **1500 requests/min**.
- Utilization = 1500 / 2000 = **0.75 = 75%**.

**Our Rules:**
- If Utilization > **85%** → **SCALE UP** (add servers) ⬆️
- If Utilization < **30%** → **SCALE DOWN** (remove servers) ⬇️
- Otherwise → **MAINTAIN** (do nothing) ➡️

### 2.3 What is "Cooldown" (Chống Flapping)?

**Problem:** Imagine load keeps bouncing:
- Minute 1: Load = 2000 → Scale UP to 3 servers.
- Minute 2: Load = 1800 → Scale DOWN to 2 servers.
- Minute 3: Load = 2100 → Scale UP to 3 servers.

This "flapping" is bad because:
- Starting a server takes time (latency).
- You pay for partial hours anyway.

**Solution:** **Cooldown Period** = Wait 5 minutes after any scaling action before allowing another.

See the implementation in [backend/autoscaler.py#L34-L43](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/backend/autoscaler.py#L34-L43).

### 2.4 What is a "Factory Pattern"?

In [models/predictor.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/models/predictor.py), we use a **Factory** to create the right model:

```python
def get_predictor(model_type: str):
    if model_type == "arima":
        return ARIMAPredictor(...)
    elif model_type == "prophet":
        return ProphetPredictor(...)
    elif model_type == "lstm":
        return LSTMPredictor(...)
```

**Why?** The API doesn't need to know HOW each model works internally. It just asks the factory: "Give me a predictor for ARIMA" and uses it.

---

## 🔥 PART 3: Detailed File Walkthroughs

### 3.1 [app.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/app.py) - The Main API

This is the **heart** of the backend. It uses **FastAPI** to create HTTP endpoints.

#### Key Sections:

| Lines | What it does |
|-------|--------------|
| 1-10 | Imports (FastAPI, Pydantic, our modules) |
| 12-20 | Logging setup (see terminal for debug info) |
| 22 | **Global `scaler` object** - keeps state across requests |
| 25-55 | **Pydantic Models** - define the shape of request/response JSON |
| 70-92 | **`/predict` endpoint** - calls AI models |
| 94-115 | **`/recommend-scaling` endpoint** - calls AutoScaler logic |
| 117-130 | **`/metrics` endpoint** - returns system health |
| 132-170 | **`/simulate` endpoint** - runs cost comparison |

#### The `/simulate` Endpoint Explained:

This is for **Phase 4 (P4)** of the project. It answers:
> "How much money would we save using AutoScaling vs. Static (fixed) servers?"

**Input:** A list of historical traffic data points.
**Logic:**
1. Loop through each minute of data.
2. For **Static**: Always assume 10 servers → Calculate cost.
3. For **AutoScaling**: Use our logic to adjust servers → Calculate cost.
4. **Savings** = Static Cost - AutoScaling Cost.

See implementation: [app.py#L132-L170](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/app.py#L132-L170)

---

### 3.2 [backend/autoscaler.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/backend/autoscaler.py) - The Brain

This is **YOUR** main contribution as M3 (Logic/Backend).

#### The `AutoScaler` Class:

| Method | Purpose |
|--------|---------|
| `__init__` | Initialize thresholds, cooldown, cost per server |
| `decide_scaling_action` | THE MAIN LOGIC: Decide scale_up/scale_down/maintain |
| `calculate_cost` | Helper to compute $ cost for N servers |

#### Key Variables:

| Variable | Default | Meaning |
|----------|---------|---------|
| `max_capacity_per_server` | 1000 | 1 server handles 1000 req/min |
| `cooldown_period` | 5 min | Wait time between scaling actions |
| `cost_per_server_hour` | $0.45 | AWS EC2-like pricing |
| `last_scale_time` | Far past | Tracks when we last scaled |

#### The Decision Logic (Pseudocode):

```
1. Is cooldown active? 
   → YES: Return "maintain" (don't scale yet)
   
2. Calculate utilization = load / capacity

3. If utilization > 85%:
   → Keep adding servers until utilization ≤ 70%
   → Return "scale_up"
   
4. If utilization < 30% AND servers > 1:
   → Remove 1 server
   → But first check: Will this cause > 80% utilization?
     → YES: Abort, return "maintain"
     → NO: Return "scale_down"
     
5. Otherwise:
   → Return "maintain"
```

---

### 3.3 [dashboard/main.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/dashboard/main.py) - The UI

This is a **Streamlit** app (Python-based web UI).

#### Key Sections:

| Lines | What it does |
|-------|--------------|
| 1-10 | Imports |
| 12-16 | Page config (title, layout) |
| 18-25 | **Sidebar controls** (model picker, refresh rate) |
| 27-40 | **Metrics display** (4 columns: Load, Servers, Cost, RMSE) |
| 42-84 | **Prediction chart** and **Scaling Recommendation** |

#### How it Connects to Backend:

The dashboard **does NOT** calculate scaling logic itself. It:
1. Calls `fetch_predictions(API_URL, ...)` → Hits `/predict` on your API.
2. Calls `fetch_scaling_recommendation(API_URL, ...)` → Hits `/recommend-scaling`.

See: [dashboard/utils/data_handler.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/dashboard/utils/data_handler.py)

---

### 3.4 [models/predictor.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/models/predictor.py) - AI Models

This is M2's territory, but you need to understand it.

#### The Abstract Base Class:

```python
class PredictionModel(ABC):
    def load_model(self, path): ...   # Load .pkl or .h5 file
    def predict(self, data, steps): ... # Return future predictions
    def get_model_name(self): ...     # Return friendly name
```

#### Current Implementations:

| Class | Model | Status |
|-------|-------|--------|
| `ARIMAPredictor` | ARIMA | 🟡 Mock (returns random) |
| `ProphetPredictor` | Facebook Prophet | 🟡 Mock |
| `LSTMPredictor` | Deep Learning | 🟡 Mock |

**Why Mock?** Real model files (`.pkl`) don't exist yet. M2 will train them. The mock data lets us test the API without crashing.

---

## 🐛 PART 4: Common Bugs & Fixes

### Bug 1: `ModuleNotFoundError: No module named 'backend'`

**Where:** When running `uvicorn app:app`

**Cause:** Python can't find the `backend` folder as a package.

**Fixes:**
1. ✅ Make sure [backend/__init__.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/backend/__init__.py) exists (even if empty).
2. ✅ Run the command **from the project root**, not from inside `backend/`.

```powershell
# ✅ CORRECT
cd d:\Downloads\dataflow\prj\autoscaling-predictor
uvicorn app:app --reload

# ❌ WRONG
cd d:\Downloads\dataflow\prj\autoscaling-predictor\backend
uvicorn app:app --reload
```

---

### Bug 2: `Connection refused` on Dashboard

**Where:** Streamlit dashboard shows "Error connecting to Backend"

**Cause:** The FastAPI server is not running.

**Fix:**
1. Open **Terminal 1**: Run `uvicorn app:app --reload --port 8000`
2. Open **Terminal 2**: Run `streamlit run dashboard/main.py`
3. Both must be running simultaneously.

---

### Bug 3: `422 Unprocessable Entity` on API calls

**Where:** When calling `/predict` or `/recommend-scaling`

**Cause:** The JSON you sent doesn't match the expected **Pydantic schema**.

**Debug Steps:**
1. Check the terminal where `uvicorn` is running. It will show the validation error.
2. Compare your JSON to the schema in [app.py#L25-L55](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/app.py#L25-L55).

**Example of correct `/predict` payload:**
```json
{
  "historical_data": [
    {"timestamp": "2026-01-27T10:00:00", "requests": 1500, "bytes": 2048}
  ],
  "forecast_window": 15,
  "model_type": "arima"
}
```

---

### Bug 4: `KeyError: 'predictions'` in Dashboard

**Where:** `dashboard/main.py` crashes when parsing API response

**Cause:** The API returned an error, not a valid prediction.

**Fix:**
1. Check Backend terminal for errors.
2. Ensure [models/predictor.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/models/predictor.py) returns the correct format:
```python
[{"timestamp": "...", "predicted_load": 123.45}, ...]
```

---

### Bug 5: Scaling Keeps Flapping (Up/Down/Up/Down)

**Where:** `/recommend-scaling` keeps changing actions every call

**Cause:** Cooldown period is not being respected.

**Debug:**
1. The cooldown only works if the **same `AutoScaler` instance** is used.
2. Check that `scaler = AutoScaler()` is **global** in [app.py#L22](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/app.py#L22), not inside a function.

**If cooldown seems broken:**
- Add debug logging in `decide_scaling_action`:
```python
logger.info(f"Time since last scale: {time_since_last_scale}")
```

---

### Bug 6: `ImportError: cannot import name 'AutoScaler'`

**Where:** When running `app.py`

**Cause:** Circular import or typo.

**Check:**
1. File is named exactly `autoscaler.py` (lowercase).
2. Class is named exactly `AutoScaler` (PascalCase).
3. Import in `app.py` is: `from backend.autoscaler import AutoScaler`

---

## ⚠️ PART 5: DEADLY Bugs (Will Break Everything)

### DEADLY 1: Editing Files While Server is Running

**Problem:** If you edit `app.py` or `autoscaler.py` and save, `uvicorn --reload` restarts. BUT if you have a **syntax error**, the server crashes.

**Prevention:**
- Always check for red squiggly lines in VS Code before saving.
- If server crashes, read the traceback carefully.

---

### DEADLY 2: Committing `.venv` or `__pycache__` to Git

**Problem:** These folders are HUGE and machine-specific.

**Fix:** Ensure [.gitignore](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/.gitignore) contains:
```
.venv/
__pycache__/
*.pyc
```

---

### DEADLY 3: Running Simulation with Empty Data

**Problem:** If you call `/simulate` with an empty list, you'll get division by zero or weird results.

**Fix:** Add validation in [app.py#L132](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/app.py#L132):
```python
if not data:
    raise HTTPException(status_code=400, detail="Data cannot be empty")
```

---

### DEADLY 4: Forgetting to Update `requirements.txt`

**Problem:** You install a new package with `pip install xyz`, but forget to add it to `requirements.txt`. Other team members can't run your code.

**Fix:** After installing anything, run:
```powershell
pip freeze > requirements.txt
```
Or manually add the package with a version number.

---

### DEADLY 5: Port Already in Use

**Problem:** `Address already in use: 8000`

**Cause:** Another process (maybe old server) is using port 8000.

**Fix (Windows PowerShell):**
```powershell
# Find the process using port 8000
netstat -ano | findstr :8000

# Kill it (replace <PID> with the number you found)
taskkill /PID <PID> /F
```

---

## 🧪 PART 6: How to Test Everything

### Test 1: Backend Health

```powershell
# Start server
uvicorn app:app --reload

# In another terminal, test health endpoint
curl http://localhost:8000/health
```

**Expected:** `{"status": "ok", "timestamp": "..."}`

---

### Test 2: Prediction Endpoint

```powershell
curl -X POST http://localhost:8000/predict `
  -H "Content-Type: application/json" `
  -d '{"historical_data": [{"timestamp": "2026-01-27T10:00:00", "requests": 100, "bytes": 1024}], "forecast_window": 5, "model_type": "arima"}'
```

**Expected:** JSON with `predictions` array.

---

### Test 3: Scaling Logic

```powershell
curl -X POST http://localhost:8000/recommend-scaling `
  -H "Content-Type: application/json" `
  -d '{"predicted_load": 2500, "current_servers": 2}'
```

**Expected:** `{"action": "scale_up", ...}` because 2500 > 85% of 2×1000.

---

### Test 4: Dashboard UI

```powershell
streamlit run dashboard/main.py
```

**Expected:** Browser opens, shows charts and metrics.

---

## 🚀 PART 7: Running the Full System

### Step-by-Step:

1. **Open Terminal 1 (Backend):**
   ```powershell
   cd d:\Downloads\dataflow\prj\autoscaling-predictor
   .\.venv\Scripts\Activate.ps1
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Open Terminal 2 (Frontend):**
   ```powershell
   cd d:\Downloads\dataflow\prj\autoscaling-predictor
   .\.venv\Scripts\Activate.ps1
   streamlit run dashboard/main.py
   ```

3. **Open Browser:**
   - API Docs: http://localhost:8000/docs (Swagger UI)
   - Dashboard: http://localhost:8501

---

## 📊 PART 8: Understanding the Simulation Results

When you call `/simulate`, you get:

| Field | Meaning |
|-------|---------|
| `static_cost` | Total $ if you ran 10 servers 24/7 |
| `auto_scaling_cost` | Total $ using our smart logic |
| `savings` | static - auto (the money you saved) |
| `savings_percentage` | Percentage saved |

**Example Result:**
```json
{
  "static_cost": 108.00,
  "auto_scaling_cost": 45.20,
  "savings": 62.80,
  "savings_percentage": 58.15
}
```

This means: **"We saved $62.80 (58%) compared to running 10 static servers!"**

---

## 📝 Quick Reference Commands

| Action | Command |
|--------|---------|
| Activate virtual environment | `.\.venv\Scripts\Activate.ps1` |
| Install dependencies | `pip install -r requirements.txt` |
| Run Backend | `uvicorn app:app --reload` |
| Run Frontend | `streamlit run dashboard/main.py` |
| View API docs | Open http://localhost:8000/docs |
| Check Python version | `python --version` |
| Freeze dependencies | `pip freeze > requirements.txt` |

---

## 🎯 Decision Guide: When to Do What

| Situation | Your Action |
|-----------|-------------|
| Model predictions are wrong | Talk to M2 (Modeler) |
| Dashboard layout needs changes | Talk to M4 (Frontend) |
| Scaling logic is wrong | Edit [backend/autoscaler.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/backend/autoscaler.py) |
| API returns errors | Check [app.py](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/app.py) |
| Missing dependencies | Edit [requirements.txt](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/requirements.txt) |
| Config values need change | Edit [config.yaml](file:///d:/Downloads/dataflow/prj/autoscaling-predictor/config.yaml) |

---

> **Last Updated:** 2026-01-27  
> **Author:** M3 (Logic/Backend)  
> **Version:** 1.0
`