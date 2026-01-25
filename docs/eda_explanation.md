# Exploratory Data Analysis (EDA) - Giải thích chi tiết

> **Lưu ý quan trọng:** EDA sử dụng dữ liệu **gốc với NaN** (không fill missing data).  
> Việc xử lý missing data chỉ áp dụng cho bước **Modeling**, không phải EDA.

---

## 1. Tại sao EDA không cần xử lý Missing Data?

### 1.1 Mục đích của EDA

| Mục đích | Cần dữ liệu gốc? |
|----------|------------------|
| Hiểu phân phối dữ liệu | ✅ Có |
| Phát hiện patterns | ✅ Có |
| Tìm outliers/anomalies | ✅ Có |
| Xác định data quality issues | ✅ Có |
| Visualize missing periods | ✅ Có |

### 1.2 Tại sao không fill trước khi EDA?

```
❌ Nếu fill missing data trước EDA:
   → Statistics bị bias (mean, std sẽ sai)
   → Không thấy được gap thực sự trong dữ liệu
   → Có thể miss important insights về data quality

✅ EDA nên dùng dữ liệu gốc:
   → Thống kê chỉ tính trên dữ liệu valid (is_outage=0)
   → Visualize rõ ràng outage period
   → Báo cáo đúng tỷ lệ missing data
```

### 1.3 Cách EDA xử lý trong code

```python
# Dữ liệu gốc (có NaN trong outage period)
df = pd.read_csv('nasa_traffic_5m.csv')

# Khi tính thống kê: loại bỏ outage rows
df_valid = df[df['is_outage'] == 0]

# Statistics được tính trên df_valid (không có NaN)
mean = df_valid['request_count'].mean()  # ✅ Chính xác
std = df_valid['request_count'].std()    # ✅ Chính xác

# Visualize: vẫn dùng df gốc để thấy gap
ax.plot(df['timestamp'], df['request_count'])  # Sẽ thấy gap
ax.axvspan(outage_start, outage_end, color='red')  # Đánh dấu outage
```

---

## 2. Pipeline: EDA vs Modeling

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA PIPELINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Raw Logs ──→ Parse ──→ Resample ──→ Mark Outage (is_outage=1) │
│                              │                                  │
│                              ▼                                  │
│              ┌───────────────────────────────┐                  │
│              │   nasa_traffic_5m.csv         │                  │
│              │   (có NaN trong outage)       │                  │
│              └───────────────────────────────┘                  │
│                       │                │                        │
│                       ▼                ▼                        │
│              ┌─────────────┐    ┌─────────────┐                 │
│              │     EDA     │    │  MODELING   │                 │
│              │  (dữ liệu   │    │  (cần fill  │                 │
│              │   gốc)      │    │   NaN)      │                 │
│              └─────────────┘    └─────────────┘                 │
│                                        │                        │
│                                        ▼                        │
│                              ┌─────────────────┐                │
│                              │ handle_missing  │                │
│                              │ _data.py        │                │
│                              │ - keep_nan()    │ → Prophet      │
│                              │ - drop_outage() │ → ARIMA        │
│                              │ - seasonal_fill │ → LSTM/XGB     │
│                              └─────────────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Chi tiết các bước EDA

### 3.1 Load Data

```python
# Load 3 resolution levels
df_1m = pd.read_csv('nasa_traffic_1m.csv')   # 89,280 rows
df_5m = pd.read_csv('nasa_traffic_5m.csv')   # 17,856 rows  ← Main
df_15m = pd.read_csv('nasa_traffic_15m.csv') # 5,952 rows
```

**Tại sao chọn 5-minute?**
- 1-minute: quá granular, nhiều noise
- 15-minute: mất detail
- 5-minute: balanced, phù hợp cho EDA và modeling

### 3.2 Basic Statistics

| Metric | Value | Note |
|--------|-------|------|
| Total records | 17,856 | 62 ngày × 288 intervals/ngày |
| Outage records | 453 (2.54%) | ~37.7 giờ |
| Valid records | 17,403 | Dùng để tính stats |

**Request Count (per 5min):**
| Statistic | Value |
|-----------|-------|
| Mean | 198.91 |
| Std | 138.40 |
| Min | 0 |
| 25% | 102 |
| 50% (Median) | 170 |
| 75% | 277 |
| Max | 1,501 |

### 3.3 Missing Data Analysis

```
Outage Period:
├── Start: 1995-08-01 14:55:00 -04:00
├── End:   1995-08-03 04:35:00 -04:00
├── Duration: 1 day 13 hours 40 minutes (~37.7 hours)
└── Cause: Server shutdown due to hurricane
```

**Tại sao cần visualize outage?**
- Để người đọc báo cáo biết có gap trong dữ liệu
- Để giải thích tại sao train/test split phải cẩn thận
- Để justify việc cần xử lý missing data cho modeling

### 3.4 Time Series Patterns

#### Daily Pattern (Hourly)
```
Traffic cao nhất: 10:00 - 16:00 EST (US business hours)
Traffic thấp nhất: 03:00 - 06:00 EST (đêm khuya)
```

**Insight:** NASA server phục vụ chủ yếu người dùng Mỹ, traffic theo múi giờ EST.

#### Weekly Pattern
```
Weekdays (Mon-Fri): Traffic cao hơn
Weekends (Sat-Sun): Traffic giảm ~20-30%
```

**Insight:** Dữ liệu từ năm 1995, khi internet chủ yếu dùng ở công sở.

### 3.5 Distribution Analysis

**Histogram insights:**
- Phân phối lệch phải (right-skewed)
- Mean (198.9) > Median (170) → có outliers cao
- Có nhiều intervals với request_count rất thấp (có thể đêm khuya)

**Box plot by month:**
- July và August có phân phối tương tự
- August có một số outliers cao hơn

### 3.6 Status Code Analysis

| Status | Percentage | Meaning |
|--------|------------|---------|
| **2xx** | 89.6% | Success - Server hoạt động tốt |
| **3xx** | 9.8% | Redirect - Chuyển hướng |
| **4xx** | 0.6% | Client Error - Request sai |
| **5xx** | 0.0% | Server Error - Rất ít |

**Insight:** Tỷ lệ error rất thấp (<1%), server NASA khá stable.

### 3.7 Spike Detection

**Method:** Threshold = Mean + 3×Std = 198.9 + 3×138.4 = **614.1**

| Metric | Value |
|--------|-------|
| Spikes detected | 140 |
| Spike percentage | 0.80% |
| Max spike | 1,501 requests/5min |

**Top spike times:** (có thể do events đặc biệt như launch, news coverage)

### 3.8 Train/Test Split

| Set | Period | Records | Percentage |
|-----|--------|---------|------------|
| **Train** | July 1 - Aug 22 | 15,264 | 85.5% |
| **Test** | Aug 23 - Aug 31 | 2,592 | 14.5% |

**Lưu ý:**
- Outage period (Aug 1-3) nằm trong **Train set**
- Test set hoàn toàn clean (không có outage)

---

## 4. Visualizations giải thích

### 4.1 Overall Traffic (01_overall_traffic.png)
- **Purpose:** Xem tổng quan traffic theo thời gian
- **Key insight:** Thấy rõ outage gap (vùng đỏ)
- **Note:** Traffic có tính seasonality rõ ràng

### 4.2 Daily Pattern (02_daily_pattern.png)
- **Purpose:** Xác định peak hours
- **Key insight:** Peak 10:00-16:00 EST
- **Use:** Autoscaling nên scale-up trước peak hours

### 4.3 Weekly Pattern (03_weekly_pattern.png)
- **Purpose:** Xác định busy days
- **Key insight:** Weekdays > Weekends
- **Use:** Có thể giảm capacity cuối tuần

### 4.4 Distribution (04_distribution.png)
- **Purpose:** Hiểu phân phối request count
- **Key insight:** Right-skewed, cần transform cho một số models
- **Use:** Xác định baseline và thresholds

### 4.5 Status Codes (05_status_codes.png)
- **Purpose:** Monitor health của server
- **Key insight:** Error rate < 1%
- **Use:** Alert nếu error rate tăng đột biến

### 4.6 Spike Detection (06_spike_detection.png)
- **Purpose:** Identify anomalies
- **Key insight:** 140 spikes (0.8%)
- **Use:** Autoscaling policy cho sudden traffic bursts

### 4.7 Train/Test Split (07_train_test_split.png)
- **Purpose:** Visualize data split
- **Key insight:** Test set clean, train set có outage
- **Use:** Validate model performance fairly

---

## 5. Kết luận

### EDA Findings Summary

1. **Data Quality:**
   - 2.54% missing (outage period)
   - < 1% errors
   - Dữ liệu tương đối clean

2. **Patterns:**
   - Strong daily seasonality (business hours)
   - Moderate weekly seasonality (weekdays > weekends)
   - Occasional spikes (0.8%)

3. **Modeling Implications:**
   - Cần model có khả năng capture seasonality (SARIMA, Prophet)
   - Cần xử lý missing data cho LSTM/XGBoost
   - Spike detection có thể dùng anomaly detection riêng

4. **Autoscaling Implications:**
   - Scale-up before 10:00 EST
   - Scale-down after 16:00 EST
   - Reduce capacity on weekends
   - Have spike handling policy (buffer capacity)

---

## 6. Files Reference

```
src/
├── eda.py                    # EDA script
└── handle_missing_data.py    # Missing data handler (for modeling)

outputs/eda/
├── 01_overall_traffic.png
├── 02_daily_pattern.png
├── 03_weekly_pattern.png
├── 04_distribution.png
├── 05_status_codes.png
├── 06_spike_detection.png
├── 07_train_test_split.png
└── eda_summary.txt

docs/
├── missing_data_strategy.md  # Chi tiết xử lý missing data
└── eda_explanation.md        # File này
```

---

*EDA sử dụng dữ liệu gốc để đảm bảo tính chính xác của phân tích. Xử lý missing data chỉ áp dụng ở bước Modeling.*
