# 🎨 Complete Beginner's Guide to the Frontend (Dashboard)

> **Purpose:** This file explains **EVERYTHING** about the User Interface (UI). It is designed for you (the expert developer) to understand the "Industrial Standard" implementation we just built.

---

## 📁 Frontend File Structure (Click to Jump)

```
autoscaling-predictor/
├── dashboard/
│   ├── main.py             # 🌟 THE DASHBOARD APP (Streamlit)
│   └── utils/
│       └── data_handler.py # 📡 API CLIENT (Talks to Backend)
└── requirements.txt        # 📦 Must include 'plotly' & 'streamlit'
```

---

## 🏗️ PART 1: The "Industrial Standard" Design Philosophy

You asked for a **Professional, Industrial Standard** UI. Here is how we achieved that in `dashboard/main.py`:

### 1.1 Custom CSS Styling (The "Glassmorphism" Look)
Standard Streamlit looks very "basic" (white background, simple text). We used **CSS Injection** to create a dark, modern theme.

**Code Location:** `dashboard/main.py` (Lines 110-210) `st.markdown("<style>...</style>")`

**Key Design Elements:**
- **Dark Mode Background:** `linear-gradient(135deg, #0e1117, #1a1a2e)` - Reduces eye strain for operators.
- **Card-Based Layout:** Each metric (Load, Cost) is in a "card" with a border and shadow (`box-shadow`). This segments information clearly.
- **Interactive Hover Effects:** When you hover over a card, it lifts up (`transform: translateY(-5px)`). This gives a "premium" feel.
- **Gradients:** Buttons and Headers use gradients (`#1f77b4` to `#2ecc71`) instead of flat colors.

### 1.2 Interactive Charts (Plotly vs Matplotlib)
We switched from `st.line_chart` (basic) to **Plotly Graph Objects** (`go.Figure`):
- **Why?** Plotly allows zooming, panning, and hovering to see exact values.
- **Reference Lines:** We added DOTTED lines for "85% Scale Up" and "30% Scale Down" thresholds directly on the chart.
- **Fill Areas:** We filled the area under the curve (`tozeroy`) to make the volume of traffic visually apparent.

### 1.3 Feedback Loops (Spinners & Status)
- **Status Dot:** Top right shows `ONLINE` (Green), `DEGRADED` (Orange), or `OFFLINE` (Red).
- **Spinners:** When fetching data, we show `st.spinner("Fetching predictions...")` so the user knows the system is working.

---

## 📚 PART 2: Code Walkthrough (`dashboard/main.py`)

### 2.1 The Imports
```python
import streamlit as st          # The UI framework
import plotly.graph_objects as go  # The Pro charting library
from utils.data_handler import ... # Our custom API functions
```
**Why separate logic?** We moved all API calls to `utils/data_handler.py` so `main.py` only cares about *displaying* data, not *fetching* it. This is **Clean Architecture**.

### 2.2 Page Config (Line 95)
```python
st.set_page_config(layout="wide", initial_sidebar_state="expanded")
```
**Industrial Tip:** Always use `layout="wide"` for dashboards. Standard width is too narrow for complex charts and 4-column metrics.

### 2.3 State Management (`st.session_state`)
Streamlit re-runs the **entire script** every time you click a button.
- **Problem:** If you enable "Auto-Refresh", how does it "remember" that it's on?
- **Solution:** `st.session_state`.
```python
if st.sidebar.checkbox("Enable Auto-Refresh"):
    st.session_state.auto_refresh = True
```
This variable survives re-runs.

### 2.4 The Metric Columns (Line 230)
We use `st.columns(4)` to create a responsive grid.
**Dynamic Logic:**
```python
load_status = "🟢" if load < 500 else "🔴"
```
We visually flag high load immediately with emojis. Operators don't read numbers; they scan for colors.

---

## 📡 PART 3: The API Bridge (`utils/data_handler.py`)

The dashboard is "Dumb". It knows nothing about AI or Scaling. It just asks the Backend.

### 3.1 Error Handling Wrapper
Every function in `data_handler.py` follows this defensive pattern:
```python
try:
    response = requests.get(...)
    if response.status_code == 200:
        return response.json()
except requests.exceptions.ConnectionError:
    st.error("🔌 Cannot connect to Backend")
```
**Why?** In an industrial setting, the backend *will* go down. The dashboard must NOT crash (Traceback); it must show a friendly "Offline" message.

### 3.2 Timeouts
```python
requests.get(..., timeout=5)
```
**Critical:** We set a 5-second timeout. If the backend hangs, the dashboard shouldn't freeze forever. It should fail fast and let the user try again.

---

## 🛠️ PART 4: Troubleshooting Guide (Frontend Specific)

### Issue 1: "ModuleNotFoundError: No module named 'plotly'"
**Cause:** You forgot to install the charting library.
**Fix:** 
```powershell
pip install plotly
```
(I have already added this to `requirements.txt` for you).

### Issue 2: "Connection refused" / "OFFLINE" Status
**Cause:** The dashboard works, but it can't find `localhost:8000`.
**Fix:**
1. Check if Backend is running (`uvicorn app:app`).
2. Check if usage of VPN or specific network configurations blocks localhost.

### Issue 3: Charts look tiny/squashed
**Cause:** You might be on mobile or a small window.
**Fix:** The CSS `div[data-testid="column"]` tries to fit contents. Maximize the window.

### Issue 4: "StreamlitAPIException: set_page_config() must be the first command"
**Cause:** You put code *before* `st.set_page_config`.
**Fix:** `set_page_config` must be the FIRST Streamlit command (after imports).

---

## 🧪 PART 5: How to Verify the "Industrial Standard"

1. **Run the App:** `streamlit run dashboard/main.py`
2. **Check the Look:** Is it dark mode? Do cards hover? (If it's white, the CSS injection failed).
3. **Test Responsiveness:** Resize the browser window. The 4 columns should stack on top of each other on mobile view.
4. **Test Interactivity:** Hover over the prediction line chart. You should see a tooltip with exact "Requests" and "Time".
5. **Test Scaling Card:** Manually lower the threshold in Backend or Mock Data to trigger "SCALE UP". The card should turn **RED** with a pulse animation.

---

## 🎯 Summary for You
- **You are M4 (Frontend) too.** You own `dashboard/`.
- **Key File:** `dashboard/main.py` is where the visual magic happens.
- **Key File:** `dashboard/utils/data_handler.py` is the "plug" that connects to the backend socket.
- **Style:** We use **CSS Injection** because Streamlit's native styling is too limited for "Industrial" requirements.

> **Final Note:** A professional dashboard is not just about data; it's about **Trust**. If it looks broken or ugly, users won't trust the AI predictions. This design builds trust.
