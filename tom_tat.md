# DATAFLOW 2026: AUTOSCALING ANALYSIS
**Đơn vị tổ chức:** CLB Toán Tin HAMIC (HUS)

## 1. TỔNG QUAN (OVERVIEW)
*   **Bối cảnh:** Quản trị hệ thống đám mây (Cloud). Cấp phát tài nguyên cố định gây lãng phí hoặc sập hệ thống.
*   **Nhiệm vụ:** Đóng vai trò Kỹ sư dữ liệu (Data Engineer/Scientist).
*   **Mục tiêu cốt lõi:**
    1.  **Bài toán Hồi quy:** Dự báo lưu lượng truy cập (Requests & Bytes).
    2.  **Bài toán Tối ưu:** Xây dựng thuật toán Autoscaling (tự động điều chỉnh số lượng máy chủ) dựa trên dự báo để tối ưu chi phí vận hành.

## 2. DỮ LIỆU (DATASET)
*   **Nguồn:** Log HTTP của máy chủ WWW trong 2 tháng.
*   **Thời gian:**
    *   Tháng 7: 01/07/1995 - 31/07/1995.
    *   Tháng 8: 01/08/1995 - 31/08/1995.
*   **Lưu ý đặc biệt (Data Gap):** Từ **14:52:01 01/08/1995** đến **04:36:13 03/08/1995** không có dữ liệu (Server tắt do bão).
*   **Định dạng:** ASCII log.
*   **Các trường thông tin cần trích xuất:**
    *   `Host`: IP/Domain.
    *   `Timestamp`: Thời gian (quan trọng cho Time Series).
    *   `Request`: Method, URL, Protocol.
    *   `HTTP Reply Code`: Status code.
    *   `Bytes`: Kích thước trả về.

## 3. YÊU CẦU KỸ THUẬT (REQUIREMENTS)

### Phần 1: Tiền xử lý (Data Engineering & EDA)
*   Xây dựng Pipeline đọc log, chuẩn hóa timestamp, parse các trường.
*   Phân tích chuỗi thời gian (Time series analysis): Hits/sec, Error rate, phát hiện Spike.
*   **Phân chia dữ liệu (Split):**
    *   **Train Set:** Tháng 7 + 22 ngày đầu tháng 8.
    *   **Test Set:** Các ngày còn lại của tháng 8.

### Phần 2: Mô hình hóa (Modeling & Forecasting)
*   **Nhiệm vụ:** Dự báo số lượng Request và số Bytes.
*   **Khung thời gian (Resample/Windowing):** Thử nghiệm trên 1 phút (1m), 5 phút (5m), 15 phút (15m).
*   **Mô hình:** Chọn tối thiểu **02 mô hình** từ các nhóm sau:
    *   Thống kê: ARIMA, SARIMA.
    *   Hiện đại: Prophet (Facebook).
    *   Deep Learning: LSTM, RNN.
    *   Machine Learning: GBDT (XGBoost, LightGBM).
*   **Metric đánh giá:** RMSE, MSE, MAE, MAPE.

### Phần 3: Bài toán Tối ưu (Optimization)
*   Thiết kế chính sách Scaling:
    *   Dựa trên luật (CPU/Request-based).
    *   Dựa trên dự báo (Predictive scaling).
*   Logic mô phỏng:
    *   Ví dụ: Scale-out khi dự báo > ngưỡng trong 5 phút.
    *   Cooldown period để tránh flapping (bật tắt liên tục).
*   Phân tích: Chi phí (Cost) vs Hiệu năng (Performance).

### Phần 4: Triển khai (Deployment & Demo)
*   **Dashboard:** Streamlit hoặc Dash (Biểu đồ tải, dự báo, đề xuất scale).
*   **API:**
    *   `/forecast`: Trả về dự báo.
    *   `/recommend-scaling`: Trả về hành động scale.
*   *(Tuỳ chọn)* Simulator giả lập hàng đợi/độ trễ.

### Điểm cộng (Bonus)
*   Phát hiện bất thường (Anomaly/DDoS detection).
*   Cơ chế Hysteresis/Cooldown thông minh.
*   Báo cáo chi phí cụ thể (Unit cost/server/giờ).

## 4. YÊU CẦU NỘP BÀI (SUBMISSION)

### Hồ sơ bao gồm:
1.  **Báo cáo (PDF):** Tối đa 30 trang (Giới thiệu, Tóm tắt, Phân tích).
2.  **Slide thuyết trình.**
3.  **Mã nguồn (GitHub Public Repo):**
    *   `README.md`: Hướng dẫn chạy, kiến trúc.
    *   Code huấn luyện/Inference.
    *   Notebook EDA.
    *   Demo App (API/UI).
4.  **Video Demo:** 3-5 phút.

### Hình thức thi:
*   Thời gian báo cáo: 20 phút (5' demo, 10' thuyết trình, 5' Q&A).
*   Ngôn ngữ: Tiếng Việt (Thuật ngữ chuyên ngành có thể dùng tiếng Anh).

## 5. TIÊU CHÍ ĐÁNH GIÁ
1.  **Tính đúng đắn & Hiệu quả:** Logic hợp lý, metric chuẩn, quy trình test chặt chẽ.
2.  **Trình bày & Demo:** Slide đẹp, demo mượt, tài liệu đầy đủ (README).
3.  **Sáng tạo & Ứng dụng:** Ý tưởng mới, khả năng mở rộng (Scalability).
4.  **Hoàn thiện:** Clean code, Reproducible (kết quả có thể tái lập).