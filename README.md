<!-- Badges -->
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/XGBoost-2.0-orange?logo=xgboost" alt="XGBoost">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

---

# 🚀 AutoScaling Predictor - NASA Log Analysis

> **Cuộc thi:** DATAFLOW 2026: THE ALCHEMY OF MINDS  
> **Đề bài:** Phân tích và Tối ưu hóa Autoscaling hệ thống dựa trên NASA Logs  
> **Câu lạc bộ:** HAMIC - Toán Tin  

---

## 👥 1. Thông tin nhóm

| Vai trò | Thành viên | Nhiệm vụ |
|---------|------------|----------|
| **M1** | [Tên] | Data Pipeline, EDA, Feature Engineering |
| **M2** | [Tên] | AI Modeling (Prophet, XGBoost) |
| **M3** | [Tên] | Backend API, AutoScaler Logic |
| **M4** | [Tên] | Frontend Dashboard, Documentation |

---

## 📖 2. Tổng quan dự án (Project Overview)

### Bài toán
Trong quản trị hệ thống đám mây, việc cấp phát tài nguyên cố định dẫn đến:
- **Lãng phí chi phí** khi lưu lượng thấp (off-peak hours)
- **Sập hệ thống** khi traffic tăng đột biến (peak hours)

### Giải pháp
Xây dựng hệ thống **AI-Powered AutoScaling** bao gồm:
1. ✅ **Data Pipeline** - Xử lý log NASA HTTP (~1.8 triệu records)
2. ✅ **AI Prediction** - Dự báo tải bằng Prophet & XGBoost
3. ✅ **AutoScaler Logic** - Thuật toán tự động scale up/down server
4. ✅ **REST API** - Backend FastAPI với Swagger documentation
5. ✅ **Web Dashboard** - Frontend hiển thị dự báo và chi phí tiết kiệm

### 🎯 Kết quả nổi bật
| Metric | Giá trị |
|--------|---------|
| **Model Accuracy (MAPE)** | 25.83% |
| **Cost Savings** | **84.3%** so với Static Deployment |
| **Monthly Savings** | **~$2,730/tháng** |

---

## 📁 3. Cấu trúc thư mục (Project Structure)

```
autoscaling/
│
├── 📄 app.py                    # 🎯 FastAPI Backend (API chính)
├── 📄 serve_frontend.py         # Server cho Frontend web
├── 📄 requirements.txt          # Dependencies
├── 📄 run_demo.bat              # ⭐ Script chạy demo (Windows)
├── 📄 README.md                 # File hướng dẫn này
│
├── 📂 frontend/                 # 🎯 FRONTEND WEB (HTML/CSS/JS)
│   ├── index.html               # Trang chính
│   ├── style.css                # Styling
│   └── app.js                   # JavaScript logic
│
├── 📂 DATA/                     # Raw data (NASA logs)
│   ├── train.txt                # Training data (Jul 1 - Aug 22)
│   └── test.txt                 # Test data (Aug 23 - Aug 31)
│
├── 📂 processed_data/           # ✅ Dữ liệu đã xử lý
│   ├── nasa_traffic_1m.csv      
│   ├── nasa_traffic_5m.csv      # File chính cho modeling
│   └── nasa_traffic_15m.csv     # File cho API demo
│
├── 📂 notebooks/                # Jupyter Notebooks
│   └── modeling_phase3.ipynb    # 🎯 NOTEBOOK CHÍNH (Train & Evaluate)
│
├── 📂 src/                      # Source code
│   ├── data_pipeline.py         # M1: Data processing pipeline
│   ├── data_processing.py       # Cleaning & parsing
│   ├── eda.py                   # Exploratory Data Analysis
│   ├── model_trainer.py         # M2: Model training
│   └── handle_missing_data.py   # Xử lý missing data (bão Aug 1-3)
│
├── 📂 models/                   # Model classes
│   └── predictor.py             # Prediction interfaces
│
├── 📂 backend/                  # Backend logic
│   └── autoscaler.py            # 🎯 M3: AutoScaler Algorithm
│
├── 📂 saved_models/             # ✅ Trained models
│   ├── xgb_requests.json        # XGBoost model (requests)
│   ├── xgb_bytes.json           # XGBoost model (bytes)
│   ├── prophet_requests.pkl     # Prophet model
│   └── metrics_summary.json     # Training metrics
│
├── 📂 dashboard/                # Streamlit Dashboard (alternative)
│   └── main.py                  
│
└── 📂 docs/                     # Documentation
    ├── eda_explanation.md
    └── missing_data_strategy.md
```

---

## ⚙️ 4. Hướng dẫn cài đặt (Installation)

### Yêu cầu hệ thống
| Yêu cầu | Phiên bản |
|---------|-----------|
| **Python** | 3.10+ |
| **RAM** | 4GB+ (khuyến nghị 8GB) |
| **OS** | Windows / Linux / MacOS |

### Bước 1: Clone repository
```bash
git clone https://github.com/[your-repo]/autoscaling.git
cd autoscaling
```

### Bước 2: Tạo Virtual Environment (khuyến nghị)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/MacOS
source venv/bin/activate
```

### Bước 3: Cài đặt thư viện
```bash
pip install -r requirements.txt
```

---

## 🚀 5. Hướng dẫn chạy chương trình (Usage)

### ⭐ Cách 1: Chạy Demo tự động (KHUYẾN NGHỊ)
```bash
# Windows - Chỉ cần double-click hoặc:
run_demo.bat
```
Script sẽ tự động:
1. Khởi động Backend API (port 8000)
2. Khởi động Frontend Web (port 3000)
3. Mở trình duyệt

### Cách 2: Chạy thủ công từng bước

#### Bước 1: Khởi động Backend API
```bash
uvicorn app:app --reload --port 8000
```
- **API Endpoint:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs

#### Bước 2: Khởi động Frontend Web
```bash
python serve_frontend.py
```
- **Dashboard:** http://localhost:3000

### Cách 3: Chạy Notebook (Xem chi tiết model)
```bash
# Mở VS Code hoặc Jupyter
jupyter notebook notebooks/modeling_phase3.ipynb
```
Chọn kernel Python và bấm **"Run All"** (~2-3 phút)

---

## 🌐 6. API Endpoints

| Endpoint | Method | Mô tả | Ví dụ |
|----------|--------|-------|-------|
| `/forecast` | GET | Dự báo traffic | `/forecast?timestamp=now&steps=4` |
| `/recommend-scaling` | GET | Khuyến nghị scaling | `/recommend-scaling?predicted_requests=2500&current_servers=2` |
| `/cost-report` | GET | Báo cáo chi phí | `/cost-report?simulation_hours=24` |
| `/metrics` | GET | System metrics | `/metrics` |
| `/health` | GET | Health check | `/health` |

### Ví dụ Response `/forecast`
```json
{
  "status": "success",
  "model": "XGBoost",
  "predictions": [
    {"timestamp": "2026-02-04T16:00:00", "predicted_requests": 853, "predicted_bytes": 16512101}
  ],
  "metrics": {"model_rmse": 43.13, "model_mape": "25.83%"}
}
```

### Ví dụ Response `/cost-report`
```json
{
  "cost_comparison": {
    "static_deployment": {"servers": 10, "total_cost": "$108.00"},
    "auto_scaling": {"total_cost": "$16.99", "avg_servers": "1.6"}
  },
  "savings": {"amount": "$91.01", "percentage": "84.3%", "monthly_projection": "$2730.38"},
  "conclusion": "AutoScaling tiết kiệm $91.01 (84.3%) trong 24 giờ."
}
```

---

## 🔬 7. Phương pháp tiếp cận (Methodology)

### 7.1 Xử lý dữ liệu (Data Processing)
- **Source:** NASA HTTP Log Dataset (Jul-Aug 1995, ~1.8M records)
- **Parsing:** Regex pattern extraction (host, timestamp, method, status, bytes)
- **Aggregation:** Resampling về khung 5 phút và 15 phút
- **Missing Data:** Xử lý gap do bão (Aug 1-3) bằng Linear Interpolation

### 7.2 Feature Engineering
| Feature | Mô tả |
|---------|-------|
| `hour`, `day_of_week` | Time-based features |
| `is_weekend` | Binary flag |
| `request_lag_1`, `lag_12`, `lag_288` | Lag features (5min, 1h, 1 day) |
| `request_rolling_mean_1h` | Rolling average |
| `hour_sin`, `hour_cos` | Cyclical encoding |

### 7.3 Mô hình AI

| Model | Lý do chọn | Ưu điểm |
|-------|------------|---------|
| **XGBoost** ⭐ | Hiệu quả cao với tabular data | MAPE thấp nhất (25.83%) |
| **Prophet** | Xử lý tốt seasonality | Robust với missing data |

### 7.4 Chiến lược AutoScaling

```
┌─────────────────────────────────────────────────────────┐
│                  AutoScaling Logic                       │
├─────────────────────────────────────────────────────────┤
│  IF utilization > 85%  →  SCALE UP (thêm server)        │
│  IF utilization < 30%  →  SCALE DOWN (bớt server)       │
│  ELSE                  →  MAINTAIN (giữ nguyên)         │
├─────────────────────────────────────────────────────────┤
│  Cooldown: 5 phút (tránh flapping)                      │
│  Capacity/server: 1000 requests/interval                │
│  Cost/server: $0.45/hour (AWS t3.medium estimate)       │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 8. Kết quả đánh giá (Evaluation)

### 8.1 Model Performance (Test Set: Aug 23-31, 1995)

| Model | Target | RMSE | MAE | MAPE |
|-------|--------|------|-----|------|
| **XGBoost** ⭐ | Requests | **43.13** | **32.36** | **25.83%** |
| Prophet | Requests | 86.63 | 63.80 | 45.05% |
| **XGBoost** ⭐ | Bytes | **1.17M** | **894K** | **39.15%** |
| Prophet | Bytes | 1.68M | 1.24M | 53.95% |

> 🏆 **Winner: XGBoost** - MAPE thấp hơn ~50% so với Prophet

### 8.2 Cost Savings Analysis (24 giờ)

| Phương án | Chi phí | Servers |
|-----------|---------|---------|
| Static Deployment | $108.00 | 10 cố định |
| **AutoScaling** | **$16.99** | Avg 1.6 |
| **Tiết kiệm** | **$91.01 (84.3%)** | - |

### 8.3 Projected Monthly Savings
```
📅 Tiết kiệm dự kiến: $2,730.38/tháng
📅 Tiết kiệm dự kiến: $32,764.56/năm
```

---

## 📚 9. Phụ lục thuật ngữ (Glossary)

| Thuật ngữ | Tiếng Việt | Giải thích |
|-----------|------------|------------|
| **AutoScaling** | Tự động co giãn | Tự động điều chỉnh số lượng server theo tải |
| **Flapping** | Dao động liên tục | Hiện tượng scale up/down liên tục gây bất ổn |
| **Cooldown** | Thời gian chờ | Khoảng nghỉ giữa các lần scaling |
| **Utilization** | Tỷ lệ sử dụng | % tài nguyên đang được sử dụng |
| **Threshold** | Ngưỡng | Giá trị kích hoạt hành động scaling |
| **EDA** | Phân tích khám phá | Exploratory Data Analysis |
| **RMSE** | Sai số bình phương | Root Mean Square Error |
| **MAE** | Sai số tuyệt đối | Mean Absolute Error |
| **MAPE** | Sai số phần trăm | Mean Absolute Percentage Error |
| **Feature Engineering** | Kỹ thuật đặc trưng | Tạo biến mới từ dữ liệu gốc |
| **Lag Features** | Đặc trưng trễ | Giá trị của biến ở các thời điểm trước |
| **Rolling Mean** | Trung bình trượt | Trung bình của N giá trị gần nhất |

---

## 🔄 10. Reproducibility Notes

### Random Seed
```python
SEED = 42
np.random.seed(SEED)
random.seed(SEED)
```

### Tested Environment
| Component | Version |
|-----------|---------|
| OS | Windows 11 |
| Python | 3.10.11 |
| FastAPI | 0.109.0 |
| XGBoost | 2.0.3 |
| Pandas | 2.2.0 |

### Data Source
- **NASA HTTP Log Dataset** (Public Domain)
- Link: https://ita.ee.lbl.gov/html/contrib/NASA-HTTP.html

---

## 📝 License

MIT License - Dự án phục vụ mục đích học tập và cuộc thi DataFlow 2026.

---

<p align="center">
  <b>🚀 AutoScaling Predictor - DataFlow 2026</b><br>
  <i>AI-Powered Server Scaling for Cost Optimization</i>
</p>
