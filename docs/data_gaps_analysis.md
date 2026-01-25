# Báo cáo phân tích Data Gaps trong NASA HTTP Logs

> **Ngày phân tích:** 25/01/2026  
> **Dataset:** NASA HTTP Server Logs (July - August 1995)

---

## 1. Tổng quan Files

| File | Kích thước | Thời gian | Số dòng (ước tính) |
|------|-----------|-----------|-------------------|
| `train.txt` | 304.88 MB | 01/Jul → 22/Aug 1995 | ~1.9 triệu |
| `test.txt` | 54.20 MB | 23/Aug → 31/Aug 1995 | ~0.5 triệu |

### Train.txt
```
First log: 01/Jul/1995:00:00:01 -0400
Last log:  22/Aug/1995:23:59:59 -0400
```

### Test.txt
```
First log: 23/Aug/1995:00:00:00 -0400
Last log:  31/Aug/1995:23:59:53 -0400
```

---

## 2. PHÁT HIỆN: 2 KHOẢNG DATA GAPS

### 2.1 Gap #1: Cuối tháng 7 (CHƯA ĐƯỢC DOCUMENT)

| Thuộc tính | Giá trị |
|------------|---------|
| **Start** | 28/Jul/1995 13:32:25 -0400 |
| **End** | 01/Aug/1995 00:00:01 -0400 |
| **Duration** | **~3.5 ngày** (khoảng 82 giờ) |
| **File ảnh hưởng** | train.txt |
| **Được đánh dấu is_outage?** | ❌ KHÔNG |

**Bằng chứng:**
```
Last log before gap:
  Line 1891714: tornado.umd.edu - [28/Jul/1995:13:32:25] "GET ..."

First log after gap:
  Line 1891715: in24.inetnebr.com - [01/Aug/1995:00:00:01] "GET ..."

Missing dates: 29/Jul, 30/Jul, 31/Jul (ENTIRE DAYS)
```

**Nguyên nhân có thể:**
- Log rotation / archiving issue
- Data collection gap
- Server maintenance không được ghi nhận
- File bị corrupt hoặc mất segment

### 2.2 Gap #2: Đầu tháng 8 - Hurricane (ĐÃ DOCUMENT)

| Thuộc tính | Giá trị |
|------------|---------|
| **Start** | 01/Aug/1995 14:52:01 -0400 |
| **End** | 03/Aug/1995 04:36:13 -0400 |
| **Duration** | **~37.7 giờ** |
| **File ảnh hưởng** | train.txt |
| **Được đánh dấu is_outage?** | ✅ CÓ |

**Bằng chứng:**
```
Last log before gap:
  Line 1925710: 192.94.94.33 - [01/Aug/1995:14:52:01] "GET ..."

First log after gap:
  Line 1925711: n1031657.ksc.nasa.gov - [03/Aug/1995:04:36:13] "GET ..."
```

**Nguyên nhân:** Server shutdown do Hurricane (bão) - đã được document trong đề bài.

---

## 3. So sánh 2 Gaps

| Thuộc tính | Gap #1 (Jul) | Gap #2 (Aug) |
|------------|--------------|--------------|
| Thời gian | ~82 giờ | ~37.7 giờ |
| Nguyên nhân | Unknown | Hurricane |
| Document? | ❌ Không | ✅ Có |
| is_outage flag? | ❌ Không | ✅ Có |
| Ảnh hưởng modeling? | ⚠️ CAO | ✅ Đã handle |

---

## 4. Ảnh hưởng đến Data Processing

### Hiện tại trong `nasa_traffic_5m.csv`:

```
Rows với request_count = 0 (không phải outage):
├── 28/Jul/1995 13:35 → 31/Jul/1995 23:55  (~1,070 rows)
├── Một số intervals rải rác khác
└── Tổng: 1,085 rows có traffic = 0 nhưng is_outage = 0
```

### Vấn đề:
1. **Model sẽ học sai** rằng traffic = 0 là bình thường
2. **Seasonality bị lệch** vì mất 3 ngày cuối tháng 7
3. **Statistics bị bias** khi tính mean/std

---

## 5. ĐỀ XUẤT XỬ LÝ

### Option A: Đánh dấu Gap #1 là outage (Recommended)

```python
# Thêm vào process_logs.py
OUTAGE_PERIODS = [
    # Gap #1: End of July (unknown cause)
    (pd.Timestamp("1995-07-28 13:32:25-04:00"), 
     pd.Timestamp("1995-07-31 23:59:59-04:00")),
    
    # Gap #2: Hurricane (documented)
    (pd.Timestamp("1995-08-01 14:52:01-04:00"), 
     pd.Timestamp("1995-08-03 04:36:13-04:00")),
]
```

**Ưu điểm:**
- Consistent handling
- Model không bị confused
- EDA statistics chính xác hơn

### Option B: Chỉ document, không sửa data

Giữ nguyên nhưng ghi nhận trong báo cáo rằng có gap chưa được handle.

### Option C: Loại bỏ toàn bộ tháng 7

Chỉ dùng data từ 01/Aug trở đi. Mất ~50% training data.

---

## 6. Timeline tổng hợp

```
July 1995
├── 01/Jul 00:00 ─────────────────────────────────── Data OK
│   ...
├── 28/Jul 13:32 ─────────────────────────────────── Last log
│   ╔══════════════════════════════════════════════╗
│   ║  GAP #1: ~82 hours (UNKNOWN CAUSE)           ║
│   ║  29/Jul, 30/Jul, 31/Jul - NO DATA            ║
│   ╚══════════════════════════════════════════════╝
August 1995
├── 01/Aug 00:00 ─────────────────────────────────── Data resumes
│   ...
├── 01/Aug 14:52 ─────────────────────────────────── Last log before storm
│   ╔══════════════════════════════════════════════╗
│   ║  GAP #2: ~37.7 hours (HURRICANE)             ║
│   ╚══════════════════════════════════════════════╝
├── 03/Aug 04:36 ─────────────────────────────────── Data resumes
│   ...
├── 22/Aug 23:59 ─────────────────────────────────── End of train.txt
│
├── 23/Aug 00:00 ─────────────────────────────────── Start of test.txt
│   ...
└── 31/Aug 23:59 ─────────────────────────────────── End of test.txt
```

---

## 7. Kết luận

### Findings:
1. ✅ **Gap #2 (Hurricane)** - Đã được document và handle đúng
2. ❌ **Gap #1 (End July)** - CHƯA được handle, cần xử lý

### Impact:
- 1,085 rows trong processed data có `request_count = 0` nhưng `is_outage = 0`
- Chiếm ~6% tổng data (ở 5-min resolution)
- Có thể gây bias cho model forecasting

### Action Required:
```
[ ] Cập nhật process_logs.py để đánh dấu Gap #1
[ ] Re-run data processing
[ ] Update EDA với thông tin mới
[ ] Document trong báo cáo cuối cùng
```

---

## 8. Code để verify

```python
import pandas as pd

df = pd.read_csv('processed_data/nasa_traffic_5m.csv', parse_dates=['timestamp'])

# Check Gap #1
gap1_start = pd.Timestamp("1995-07-28 13:30:00", tz='UTC-04:00')
gap1_end = pd.Timestamp("1995-08-01 00:00:00", tz='UTC-04:00')

gap1 = df[(df['timestamp'] >= gap1_start) & (df['timestamp'] < gap1_end)]
print(f"Gap #1 rows: {len(gap1)}")
print(f"Zero traffic rows: {(gap1['request_count'] == 0).sum()}")
print(f"is_outage = 1: {(gap1['is_outage'] == 1).sum()}")
```

---

*Báo cáo này được tạo sau khi phân tích files train.txt và test.txt gốc.*
