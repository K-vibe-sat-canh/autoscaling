# 🚀 AutoScaling Predictor - DataFlow 2026

> **Đề bài:** Autoscaling Analysis  
> **Cuộc thi:** DataFlow 2026: The Alchemy of Minds  
> **Câu lạc bộ:** HAMIC - Toán Tin

---

## 📋 Mục lục

1. [Giới thiệu](#giới-thiệu)
2. [Cài đặt](#cài-đặt)
3. [Hướng dẫn chạy](#hướng-dẫn-chạy)
4. [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
5. [Kết quả](#kết-quả)
6. [Thành viên](#thành-viên)
7. [Tài liệu kỹ thuật - Regex Parsing](#tài-liệu-kỹ-thuật---regex-parsing)

---

## 📖 Giới thiệu

### Bài toán
Trong quản trị hệ thống đám mây, việc cấp phát tài nguyên cố định dẫn đến:
- **Lãng phí** khi ít người truy cập
- **Sập hệ thống** khi traffic tăng đột biến

### Giải pháp
Xây dựng hệ thống **AI dự đoán traffic** + **Logic tự động điều chỉnh số server** để:
- Tối ưu chi phí vận hành
- Đảm bảo hiệu năng hệ thống

### Công nghệ sử dụng
| Thành phần | Công nghệ |
|------------|-----------|
| Data Pipeline | Python, Pandas, NumPy |
| AI Models | **Prophet**, **XGBoost**, ARIMA |
| Backend API | FastAPI, Uvicorn |
| Dashboard | Streamlit, Plotly |
| Visualization | Matplotlib, Plotly |

---

## ⚙️ Cài đặt

### Prerequisites (Yêu cầu hệ thống)
| Yêu cầu | Phiên bản/Giá trị |
|---------|-------------------|
| Python | 3.10+ |
| RAM | Tối thiểu 4GB |
| OS | Windows / Linux / MacOS |

### Các bước

```bash
# 1. Clone repository
git clone <repo-url>
cd uibackend

# 2. Tạo virtual environment (khuyên dùng)
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 3. Cài đặt dependencies
pip install -r requirements.txt
```

---

## 🚀 Hướng dẫn chạy

### ⭐ Option A: Chạy Notebook (KHUYẾN NGHỊ CHO GIÁM KHẢO)

**Bước 1:** Mở VS Code hoặc Jupyter Notebook

**Bước 2:** Mở file `notebooks/modeling_phase3.ipynb`

**Bước 3:** Chọn kernel `.venv (Python 3.10.11)` hoặc `autoscaling`

**Bước 4:** Bấm **"Run All"** để chạy từ đầu đến cuối

> ⏱️ **Thời gian dự kiến:** ~2-3 phút trên CPU

**Output bao gồm:**
- ✅ Model comparison table (RMSE, MAE, MAPE)
- ✅ Visualization: Actual vs Predicted (Prophet & XGBoost)
- ✅ Feature Importance chart
- ✅ Autoscaling simulation results

---

### Option B: Chạy từng bước

#### Bước 1: Tạo dữ liệu (M1) - Đã có sẵn
```bash
# Dữ liệu đã được xử lý sẵn tại processed_data/
# Nếu cần chạy lại:
python src/data_processing.py
```

#### Bước 2: Train model (M2)
```bash
# Cách 1: Chạy notebook (khuyến nghị)
jupyter notebook notebooks/modeling_phase3.ipynb

# Cách 2: Chạy script
python src/model_trainer.py
# Output: saved_models/*.pkl, saved_models/*.json
```

### Bước 3: Chạy Backend API (M3)
```bash
uvicorn app:app --reload
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Bước 4: Chạy Dashboard (M4)
```bash
streamlit run dashboard/main.py
# Dashboard: http://localhost:8501
```

### Chạy tất cả (Windows)
```bash
run_all.bat
```

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐    HTTP    ┌─────────────────┐
│   Dashboard     │ ◄────────► │   Backend API   │
│   (Streamlit)   │            │   (FastAPI)     │
└─────────────────┘            └─────────────────┘
                                      │
                                      ▼
                               ┌─────────────────┐
                               │   AI Models     │
                               │   (ARIMA)       │
                               └─────────────────┘
                                      │
                                      ▼
                               ┌─────────────────┐
                               │   Data          │
                               │   (clean.csv)   │
                               └─────────────────┘
```

### Cấu trúc thư mục

```
uibackend/
├── app.py                  # FastAPI Backend
├── config.yaml             # Configuration
├── requirements.txt        # Dependencies
├── README.md               # File này
├── run_all.bat             # Script chạy tất cả (Windows)
│
├── DATA/                   # Raw data (NASA logs .txt)
│   ├── train.txt
│   └── test.txt
│
├── processed_data/         # ✅ Dữ liệu đã xử lý (CSV)
│   ├── nasa_traffic_1m.csv
│   ├── nasa_traffic_5m.csv   # 🎯 File chính cho modeling
│   └── nasa_traffic_15m.csv
│
├── notebooks/
│   └── modeling_phase3.ipynb # 🎯 NOTEBOOK CHÍNH - Chạy file này!
│
├── src/
│   ├── data_pipeline.py    # M1: Data Processing
│   ├── data_processing.py  # Data cleaning
│   ├── eda.py              # Exploratory Data Analysis
│   └── model_trainer.py    # M2: Model Training
│
├── models/
│   └── predictor.py        # Prediction model classes
│
├── backend/
│   └── autoscaler.py       # M3: Scaling Logic
│
├── dashboard/
│   └── main.py             # Streamlit Dashboard
│
├── saved_models/           # ✅ Models đã train
│   ├── prophet_requests.pkl
│   ├── prophet_bytes.pkl
│   ├── xgb_requests.json
│   ├── xgb_bytes.json
│   └── metrics_summary.json
│
├── outputs/
│   └── eda/                # EDA plots và summary
│
└── docs/                   # Documentation
```

---

## 📊 Data Description

### Nguồn dữ liệu
- **NASA HTTP Log Dataset** (Public Domain)
- Link: https://ita.ee.lbl.gov/html/contrib/NASA-HTTP.html

### Thông tin dữ liệu
| Thuộc tính | Giá trị |
|------------|---------|
| Thời gian | July 1 - August 31, 1995 |
| Tổng records | ~1.8 triệu requests |
| Missing gap | Aug 1 (14:52) - Aug 3 (04:36) do bão |
| Aggregation | 5 phút (288 intervals/ngày) |

### Train/Test Split (Theo yêu cầu đề bài)
| Set | Thời gian | Số samples (5min) |
|-----|-----------|-------------------|
| **Train** | July 1 → August 22, 1995 | 15,264 |
| **Test** | August 23 → August 31, 1995 | 2,592 |

---

## 📊 Kết quả Model (Test Set: Aug 23 - Aug 31)

### Model Comparison

| Model | Target | RMSE | MAE | MAPE |
|-------|--------|------|-----|------|
| **XGBoost** ⭐ | Request Count | **43.13** | **32.36** | **25.83%** |
| Prophet | Request Count | 86.63 | 63.80 | 45.05% |
| **XGBoost** ⭐ | Total Bytes | **1.17M** | **894K** | **39.15%** |
| Prophet | Total Bytes | 1.68M | 1.24M | 53.95% |

> 🏆 **Winner: XGBoost** với MAPE thấp hơn ~50% so với Prophet

### Feature Importance (XGBoost)
Top 5 features quan trọng nhất:
1. `request_lag_1` - Lag 1 interval (5 min trước)
2. `request_rolling_mean_1h` - Trung bình 1 giờ gần nhất
3. `request_lag_288` - Lag 1 ngày (288 intervals)
4. `hour` - Giờ trong ngày
5. `request_lag_12` - Lag 1 giờ

### Autoscaling Simulation

| Tham số | Giá trị |
|---------|---------|
| Capacity/server | 500 requests/5min |
| Scale up threshold | 80% utilization |
| Scale down threshold | 30% utilization |
| Cooldown period | 30 phút (6 intervals) |

**Kết quả:**
- Scale up events: 5
- Scale down events: 6
- Server range: 1-2 servers

### Cost Simulation
| Phương án | Chi phí (24h) |
|-----------|---------------|
| Static (10 servers) | $108.00 |
| AutoScaling | ~$45.00 |
| **Tiết kiệm** | **~58%** |

---

## 👥 Thành viên

| Vai trò | Tên | Công việc |
|---------|-----|-----------|
| M1 | Data Cleaning | Parse log, EDA, Feature Engineering |
| M2 | Modeler | Train ARIMA, Evaluate metrics |
| M3 | Logic/Backend | AutoScaler class, FastAPI |
| M4 | Support & FE | Streamlit Dashboard, Docs |

---

## 📝 Tài liệu kỹ thuật - Regex Parsing

### Regex Logic cho NASA HTTP Logs

#### Giai đoạn 1: Parse dòng Log
**Pattern:** `^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"([^"]*)"\s+(\d{3})\s+(\S+)\s*$`

| Phần | Mô tả |
|------|-------|
| `^(\S+)` | Host/IP |
| `\[([^\]]+)\]` | Timestamp |
| `"([^"]*)"` | Request String |
| `(\d{3})` | Status Code |
| `(\S+)` | Bytes |

#### Giai đoạn 2: Tách Request
**Pattern:** `^(\S+)\s+(\S+)(?:\s+(\S+))?$`

```python
import re

LOG_RE = re.compile(
    r'^(?P<host>\S+)\s+\S+\s+\S+\s+\[(?P<ts>[^\]]+)\]\s+'
    r'"(?P<request>[^"]*)"\s+(?P<status>\d{3})\s+(?P<bytes>\S+)\s*$'
)

REQ_RE = re.compile(
    r'^(?P<method>\S+)\s+(?P<url>\S+)(?:\s+(?P<protocol>\S+))?$'
)
```

---

## � Reproducibility Notes

### Random Seed
```python
SEED = 42
np.random.seed(SEED)
random.seed(SEED)
```

### Đường dẫn
- ✅ Sử dụng **relative paths** (không hard-code absolute paths)
- ✅ Compatible với Windows/Linux/MacOS

### Tested Environment
- OS: Windows 11
- Python: 3.10.11
- RAM: 8GB

---

## �📝 License

MIT License - Dự án phục vụ mục đích học tập và cuộc thi DataFlow 2026.
