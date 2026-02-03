# 📊 Slide Ideas for Presentation (20 minutes)

> **Note to presenter:** This is a guide for building your slides. The presentation is 20 minutes:
> - 5 min: Demo sản phẩm
> - 10 min: Thuyết trình
> - 5 min: Vấn đáp

---

## Slide 1: Title
- **Title:** AutoScaling Predictor - Tối ưu chi phí Cloud bằng AI
- **Subtitle:** DataFlow 2026: The Alchemy of Minds
- **Team name / Members**
- **Logo HAMIC**

---

## Slide 2: Vấn đề (Problem Statement)
- **Hình ảnh:** Server farm với mũi tên lên/xuống
- **2 vấn đề chính:**
  1. 🔴 Traffic thấp → Lãng phí tiền
  2. 🔴 Traffic cao → Crash hệ thống
- **Quote:** "Dự đoán traffic để scale đúng lúc, đúng lượng"

---

## Slide 3: Giải pháp tổng quan
- **Diagram kiến trúc 3 thành phần:**
  1. 📊 Data Pipeline (Xử lý log)
  2. 🧠 AI Model (Dự đoán traffic)
  3. ⚡ AutoScaler (Quyết định scale)
- **Flow:** Data → Model → Decision → Action

---

## Slide 4: Data Pipeline (M1)
- **Input:** ASCII log files (July-August 1995)
- **Processing:**
  - Regex parse fields (IP, URL, Bytes)
  - Handle "Storm" period (01/08 - 03/08)
  - Resample to 1m/5m/15m
- **Output:** clean_data.csv (86,400 rows)

---

## Slide 5: AI Model Selection (M2)
- **Models thử nghiệm:**
  | Model | Pros | Cons | RMSE |
  |-------|------|------|------|
  | ARIMA | Fast, Interpretable | Linear only | 177 |
  | Prophet | Handles seasonality | Heavier | TBD |
  | LSTM | Non-linear | Slow training | TBD |
- **Kết luận:** ARIMA đủ tốt cho bài toán này

---

## Slide 6: ARIMA Explained (Đơn giản)
- **Hình ảnh:** Sóng sine với annotation
- **3 components:**
  - AR: "Hôm qua bận → Hôm nay có thể bận"
  - I: "Traffic tăng dần theo tuần"
  - MA: "Điều chỉnh dựa trên sai số trước"
- **Parameters:** ARIMA(5, 1, 0)

---

## Slide 7: AutoScaler Logic (M3)
- **Flowchart:**
  ```
  Predicted Load
       │
       ▼
  ┌──────────┐
  │ >85% ?   │──Yes──► SCALE UP
  └──────────┘
       │No
       ▼
  ┌──────────┐
  │ <30% ?   │──Yes──► SCALE DOWN
  └──────────┘
       │No
       ▼
    MAINTAIN
  ```
- **Highlight:** Cooldown 5 phút chống flapping

---

## Slide 8: Cost Simulation Results
- **Chart:** Bar chart so sánh
  - Static (10 servers): $108/day
  - AutoScaling: $45/day
  - **Savings: 58%**
- **Highlight số lớn:** "TIẾT KIỆM 63$ MỖI NGÀY!"

---

## Slide 9: Dashboard Demo (Screenshot)
- **Screenshot:** Dashboard với 3 panels
  1. Metrics cards (Load, Servers, Cost)
  2. Prediction chart (với threshold lines)
  3. Scaling recommendation card
- **Note:** Demo live sẽ show interactive features

---

## Slide 10: Technical Stack
- **Logos grid:**
  - Python | Pandas | NumPy
  - FastAPI | Streamlit | Plotly
  - statsmodels | ARIMA
- **Highlight:** 100% Python, No cloud vendor lock-in

---

## Slide 11: Demo Plan (5 minutes)
1. **Show Dashboard** (1 min)
   - Explain metrics
   - Click "Generate Prediction"
2. **Show Scaling Card** (1 min)
   - Trigger a scale-up scenario
3. **Show Simulation** (1 min)
   - Run cost comparison
4. **Show API Docs** (1 min)
   - /docs endpoint
5. **Q&A prep** (1 min)

---

## Slide 12: Future Work
- ✅ Done: Basic ARIMA + AutoScaler
- 🔄 In Progress: Prophet comparison
- 📋 Todo:
  - LSTM for complex patterns
  - Anomaly detection (DDoS)
  - Multi-region scaling

---

## Slide 13: Conclusion
- **Key takeaways:**
  1. AI có thể dự đoán traffic với RMSE < 200
  2. AutoScaling tiết kiệm 50-60% chi phí
  3. Cooldown logic rất quan trọng
- **Call to action:** "Questions?"

---

## Slide 14: Q&A
- **Hình ảnh:** Team logo / Contact info
- **Backup slides sẵn sàng:**
  - ARIMA math details
  - Code snippets
  - Error handling
