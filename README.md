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
| Data Pipeline | Python, Pandas |
| AI Model | ARIMA (statsmodels) |
| Backend API | FastAPI |
| Dashboard | Streamlit, Plotly |

---

## ⚙️ Cài đặt

### Yêu cầu
- Python 3.10+
- pip

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

### Bước 1: Tạo dữ liệu (M1)
```bash
python src/data_pipeline.py
# Output: data/clean_data.csv
```

### Bước 2: Train model (M2)
```bash
python src/model_trainer.py
# Output: saved_models/arima_model.pkl
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
├── dashboard/
│   └── main.py             # Streamlit Dashboard
├── data/
│   └── clean_data.csv      # Dữ liệu đã xử lý
├── saved_models/
│   └── arima_model.pkl     # Model đã train
├── src/
│   ├── data_pipeline.py    # M1: Data Processing
│   └── model_trainer.py    # M2: Model Training
├── backend/
│   └── autoscaler.py       # M3: Scaling Logic
├── docs/                   # Documentation
├── notebooks/              # EDA Notebooks
├── requirements.txt        # Dependencies
└── README.md               # File này
```

---

## 📊 Kết quả

### Model Performance (ARIMA)
| Metric | Giá trị |
|--------|---------|
| RMSE | ~475 requests/min |
| MAE | ~350 requests/min |
| MAPE | ~14% |

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

## 📝 License

MIT License - Dự án phục vụ mục đích học tập và cuộc thi DataFlow 2026.
