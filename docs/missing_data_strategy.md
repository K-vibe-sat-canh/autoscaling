# Chiến lược xử lý Resample & Missing Data

> **Bài toán:** Dự báo lưu lượng truy cập (request_count, total_bytes) cho hệ thống Autoscaling  
> **Dataset:** NASA HTTP Logs (July-August 1995)  
> **Vấn đề:** Server down do bão từ 14:52 01/08 đến 04:36 03/08 (~37.7 giờ)

---

## 1. Tổng quan dữ liệu

### 1.1 Thống kê cơ bản

| Metric | Giá trị |
|--------|---------|
| Tổng thời gian | 01/07/1995 → 31/08/1995 (62 ngày) |
| Outage period | 14:52 01/08 → 04:36 03/08 |
| Thời gian mất dữ liệu | **~37.7 giờ** (2,264 phút) |
| Tỷ lệ missing | 2.5% tổng số rows |

### 1.2 Các file đã resample

```
processed_data/
├── nasa_logs_parsed.csv     # Raw log đã parse (chi tiết)
├── nasa_traffic_1m.csv      # 89,280 rows - Phân tích spike
├── nasa_traffic_5m.csv      # ~17,856 rows - Training chính
└── nasa_traffic_15m.csv     # ~5,952 rows - ARIMA nhanh
```

### 1.3 Cấu trúc dữ liệu sau resample

| Column | Type | Mô tả |
|--------|------|-------|
| `timestamp` | datetime | Mốc thời gian |
| `request_count` | float | Số lượng request trong interval |
| `total_bytes` | float | Tổng bytes trả về |
| `status_2xx` | float | Số request thành công |
| `status_3xx` | float | Số redirect |
| `status_4xx` | float | Số client error |
| `status_5xx` | float | Số server error |
| `is_outage` | int | Flag: 1 = server down, 0 = bình thường |

---

## 2. Vấn đề Missing Data

### 2.1 Nguyên nhân

```
Server NASA bị tắt do bão (hurricane) từ:
  Start: 1995-08-01 14:52:01 -0400
  End:   1995-08-03 04:36:13 -0400
  
Khoảng thời gian này KHÔNG có log nào được ghi nhận.
```

### 2.2 Tại sao không thể bỏ qua?

1. **Time series cần liên tục**: Nhiều model (LSTM, ARIMA) yêu cầu dữ liệu không có gap
2. **37 giờ là quá dài**: Không thể đơn giản forward-fill vì sẽ tạo fake pattern
3. **Ảnh hưởng đến seasonality**: Mất 1.5 ngày sẽ làm lệch daily/weekly pattern

---

## 3. Các chiến lược xử lý

### 3.1 Strategy 1: Giữ NaN (Keep NaN)

```python
# Không làm gì, giữ NaN trong outage period
df = handler.keep_nan()
```

| Ưu điểm | Nhược điểm |
|---------|------------|
| ✅ Không tạo fake data | ❌ Một số model không chấp nhận NaN |
| ✅ Prophet tự xử lý được | ❌ Phải handle riêng khi visualize |
| ✅ Trung thực với dữ liệu | |

**Best for:** Prophet, ARIMA (với proper handling)

---

### 3.2 Strategy 2: Drop Outage Period

```python
# Xóa hoàn toàn các rows có is_outage = 1
df = handler.drop_outage()
```

| Ưu điểm | Nhược điểm |
|---------|------------|
| ✅ Dữ liệu sạch, không NaN | ❌ Mất tính liên tục thời gian |
| ✅ Đơn giản nhất | ❌ Model có thể học sai transition |
| ✅ Không bias từ fake data | ❌ Mất 2,264 data points |

**Best for:** Phân tích EDA, baseline models

---

### 3.3 Strategy 3: Seasonal Interpolation ⭐ **RECOMMENDED**

```python
# Fill NaN bằng mean của cùng (hour, minute, dayofweek)
df = handler.seasonal_interpolation()
```

**Logic:**
```
NaN lúc 15:00 Thứ 3 ngày 01/08
  → Lấy mean(request_count) của tất cả 15:00 Thứ 3 từ dữ liệu có sẵn
  → Fill vào vị trí NaN
```

| Ưu điểm | Nhược điểm |
|---------|------------|
| ✅ Giữ được daily pattern | ❌ Phức tạp hơn |
| ✅ Giữ được weekly pattern | ❌ Giả định pattern không đổi |
| ✅ Model nhận input hoàn chỉnh | ❌ Vẫn là "estimated" data |
| ✅ Mean gần với ground truth | |

**Best for:** LSTM, XGBoost, Neural Networks

---

### 3.4 Strategy 4: Fill với 0 ❌ **KHÔNG KHUYẾN NGHỊ**

```python
# KHÔNG NÊN DÙNG
df[metrics] = df[metrics].fillna(0)
```

**Vấn đề nghiêm trọng:**
- `request_count = 0` có 2 nghĩa:
  1. Server **đang chạy** nhưng không có ai truy cập
  2. Server **đã down** nên không có log
- Model sẽ học nhầm rằng "có lúc traffic = 0 là bình thường"
- Autoscaling có thể scale-down sai khi thấy traffic thấp

---

## 4. So sánh kết quả

### 4.1 Mean request_count

| Strategy | Mean | NaN Count | Note |
|----------|------|-----------|------|
| Original (NaN) | 39.78 | 2,264 | Baseline |
| Drop outage | 39.78 | 0 | Mất rows |
| Seasonal fill | 39.98 | 0 | Slight increase |
| Fill 0 | 38.77 | 0 | ❌ Biased low |

### 4.2 Sample: Outage boundary

```
                  timestamp  original  seasonal_fill  is_outage
1995-08-01 14:50:00-04:00       0.0           0.0          0
1995-08-01 14:51:00-04:00       0.0           0.0          0
1995-08-01 14:52:00-04:00       1.0           1.0          0
1995-08-01 14:53:00-04:00       NaN          75.8          1  ← Start outage
1995-08-01 14:54:00-04:00       NaN          87.1          1
1995-08-01 14:55:00-04:00       NaN          79.1          1
...
1995-08-03 04:36:00-04:00       NaN          xx.x          1  ← End outage
1995-08-03 04:37:00-04:00       1.0           1.0          0
```

---

## 5. Khuyến nghị theo Model

### 5.1 Bảng tổng hợp

| Model | Strategy | Lý do |
|-------|----------|-------|
| **Prophet** | Keep NaN | Prophet xử lý NaN như "holiday", học pattern từ data có sẵn |
| **ARIMA/SARIMA** | Drop outage hoặc Seasonal fill | Cần series liên tục |
| **LSTM/RNN** | Seasonal interpolation | Input không được có NaN |
| **XGBoost/LightGBM** | Seasonal fill + `is_outage` feature | Có thể học pattern từ flag |
| **Simple Baseline** | Drop outage | Đơn giản, clear |

### 5.2 Code sử dụng

```python
from src.handle_missing_data import MissingDataHandler

# Load data
handler = MissingDataHandler('processed_data/nasa_traffic_5m.csv')

# Cho Prophet
df_prophet = handler.keep_nan()

# Cho LSTM/XGBoost  
df_ml = handler.seasonal_interpolation()

# Split train/test theo đề bài
train, test = handler.get_train_test_split(df_ml)
# Train: 01/07 → 22/08 (76,320 rows @ 1m)
# Test:  23/08 → 31/08 (12,960 rows @ 1m)
```

---

## 6. Lưu ý quan trọng

### 6.1 Giữ `is_outage` làm feature

Dù dùng strategy nào, **luôn giữ cột `is_outage`** vì:
- Model có thể học rằng sau outage, traffic có pattern khác
- Dùng cho anomaly detection
- Báo cáo/dashboard cần hiển thị period này

### 6.2 Không nên làm

❌ Forward fill 37 giờ liên tục  
❌ Fill 0 vào outage  
❌ Xóa cột `is_outage` sau khi fill  
❌ Linear interpolation (sẽ smooth mất pattern)

### 6.3 Nên làm

✅ Dùng `is_outage` như feature bổ sung  
✅ Report rõ strategy đã dùng trong báo cáo  
✅ So sánh kết quả với/không có seasonal fill  
✅ Visualize riêng outage period trong dashboard

---

## 7. Kết luận

### Giải pháp tốt nhất: **Seasonal Interpolation + is_outage flag**

```
Lý do:
1. Giữ được seasonality pattern (daily, weekly)
2. Không tạo bias như fill 0
3. Model nhận được input hoàn chỉnh
4. Vẫn có thể identify outage period qua flag
5. Mean sau fill (39.98) gần với original (39.78)
```

### Workflow đề xuất

```
Raw logs → Parse → Resample (1m/5m/15m) → Mark outage
                                              ↓
                    ┌─────────────────────────┴─────────────────────────┐
                    ↓                                                   ↓
            [Prophet/ARIMA]                                    [LSTM/XGBoost]
            Keep NaN as-is                                 Seasonal interpolation
                    ↓                                                   ↓
                 Train                                               Train
                    ↓                                                   ↓
               Forecast ──────────────────→ Ensemble ←──────────────── Forecast
                                               ↓
                                        Autoscaling Decision
```

---

*File này được tạo tự động. Xem chi tiết implementation tại `src/handle_missing_data.py`*
