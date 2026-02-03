DATAFLOW SEASON 2: QUY ĐỊNH VỀ “**REPRODUCIBILITY”** (TÍNH TÁI LẬP)

**CẢNH BÁO QUAN TRỌNG:**

Một giải pháp xuất sắc nhưng **không chạy được trên máy của Giám khảo/BTC** có nguy cơ bị đánh giá là **KHÔNG HỢP LỆ** ở tiêu chí "Tính hoàn thiện" (chiếm 10% tổng điểm).

Để đảm bảo quyền lợi cho chính mình và giúp BTC chấm thi công bằng, nhanh chóng, **khuyến khích** các đội thi tuân thủ các quy định kỹ thuật sau:

## ---

**1\. NGUYÊN TẮC VÀNG: "NO HARD-CODING"**

Tuyệt đối **KHÔNG** sử dụng đường dẫn tuyệt đối (Absolute Paths) trỏ đến thư mục cá nhân trên máy của bạn.

* ❌ **SAI:** df \= pd.read\_csv("C:/Users/Tuan/Desktop/DataFlow/data/train.csv")  
* ✅ **ĐÚNG:** df \= pd.read\_csv("./data/train.csv") hoặc sử dụng biến môi trường.  
* ✅ **KHUYẾN NGHỊ:** Sử dụng module os hoặc pathlib trong Python để xử lý đường dẫn tương thích giữa Windows/Linux/MacOS.

## ---

**2\. QUY ĐỊNH DÀNH CHO NOTEBOOK (Colab / Jupyter)**

*(Áp dụng chính cho: Learning Prediction & Phần Modeling của Autoscaling)*

Nếu nộp bài bằng Jupyter Notebook (.ipynb), bạn phải đảm bảo:

1. **Chạy tuần tự (Sequential Execution):** Notebook phải chạy thành công từ trên xuống dưới (Cell 1 → Cell n) khi bấm "Run All". Không được có trường hợp Cell ở dưới định nghĩa biến cho Cell ở trên.  
2. **Cố định hạt giống (Random Seed):** Để kết quả huấn luyện mô hình (Model Training) giống nhau mỗi lần chạy, bắt buộc phải set seed ngay đầu file:  
   Python  
   import numpy as np  
   import random  
   import tensorflow as tf \# hoặc torch  
   SEED \= 42  
   np.random.seed(SEED)  
   random.seed(SEED)  
   tf.random.set\_seed(SEED)

3. **Dependencies:**  
   * Liệt kê rõ các thư viện cần cài đặt ở cell đầu tiên hoặc file requirements.txt.  
   * Nếu dùng Colab, hãy để sẵn dòng lệnh cài đặt (đã comment hoặc active): \!pip install \-r requirements.txt.  
4. **Đường dẫn Data:** Nếu chạy trên Colab và cần mount Google Drive, hãy viết code thông minh để check môi trường:  
   Python  
   import os  
   if 'google.colab' in str(get\_ipython()):  
       from google.colab import drive  
       drive.mount('/content/drive')  
       BASE\_DIR \= '/content/drive/MyDrive/DataFlow\_TeamX'  
   else:  
       BASE\_DIR \= './'

## ---

**3\. QUY ĐỊNH DÀNH CHO HỆ THỐNG FULLSTACK & APP (Docker)**

*(Áp dụng chính cho: Fullstack Lakehouse & Phần Dashboard của Autoscaling)*

1. **Docker hóa (Dockerize) là ưu tiên số 1:**  
   * Khuyến khích tối đa việc nộp file docker-compose.yml. BTC sẽ ưu tiên chấm bằng lệnh docker-compose up \-d.  
   * Đảm bảo file Dockerfile build thành công, không bị lỗi version hệ điều hành.  
2. **Cấu hình Môi trường (.env):**  
   * Tuyệt đối **KHÔNG** hard-code mật khẩu, API Key, hay các port nhạy cảm trong code.  
   * Tạo file .env.example chứa các biến môi trường mẫu.  
   * Trong README.md, hướng dẫn BTC: "Copy file .env.example thành .env rồi chạy lệnh..."  
3. **Xử lý Dữ liệu lớn & Service:**  
   * Với đề Lakehouse: Script khởi tạo (init script) để tạo bucket MinIO, tạo bảng Iceberg ban đầu nên được tự động hóa (VD: bỏ vào thư mục /docker-entrypoint-initdb.d hoặc chạy một container setup).  
   * Nếu hệ thống quá nặng (VD: Spark \+ Clickhouse \+ Superset), hãy ghi chú rõ trong README về cấu hình RAM tối thiểu (VD: "Cần tối thiểu 8GB RAM để chạy mượt").

## ---

**4\. QUY ĐỊNH VỀ DỮ LIỆU & TÀI NGUYÊN (DATA & RESOURCES)**

1. **Dữ liệu ngoài (External Data):**  
   * Nếu sử dụng dữ liệu ngoài (Open Data), **BẮT BUỘC** phải dẫn nguồn công khai (link tải) trong báo cáo.  
   * Nếu dữ liệu đã được tiền xử lý (pre-processed) và lưu thành file mới (VD: clean\_data.parquet), hãy upload lên Google Drive/OneDrive, để chế độ "Public" và gắn link vào file README.md hoặc script tải dữ liệu tự động (download\_data.sh).  
2. **Model Pre-trained:**  
   * Với các file model nặng (\>100MB), **KHÔNG** push lên GitHub. Hãy upload lên Drive và cung cấp link tải.  
   * Khuyến khích viết script tự động tải model về đúng thư mục.

## ---

**5\. QUYỀN SỞ HỮU TRÍ TUỆ (IP RIGHTS)**

* **Quyền tác giả:** Mã nguồn (Source code) và giải pháp thuộc quyền sở hữu trí tuệ của đội thi (Sinh viên).  
* **Quyền sử dụng:** Bằng việc nộp bài, đội thi đồng ý cấp quyền cho BTC và các Nhà tài trợ được phép sử dụng, sao chép, nghiên cứu mã nguồn cho mục đích chấm thi, truyền thông, và phi thương mại trong khuôn khổ cuộc thi.  
* Mọi hành vi sao chép code của đội khác hoặc gian lận từ các nguồn không công khai sẽ bị xử lý theo quy chế.

## ---

**6\. CHECKLIST BẮT BUỘC TRONG FILE README.md**

Mỗi Repository nộp về phải có file README.md ở thư mục gốc, trình bày tối thiểu các mục sau (để Sinh viên chấm thi có thể làm theo):

1. **Project Title:** Tên đội \- Tên đề tài.  
2. **Prerequisites:** Yêu cầu cài đặt (Python version bao nhiêu? Cần cài Docker không? RAM tối thiểu?).  
3. **Installation:**  
   * Lệnh cài thư viện: pip install \-r requirements.txt  
   * Lệnh build docker: docker-compose build  
4. **How to Run (QUAN TRỌNG NHẤT):**  
   * Bước 1: Chạy file nào để tiền xử lý dữ liệu?  
   * Bước 2: Chạy file nào để training (hoặc load model)?  
   * Bước 3: Chạy file nào để lên Dashboard/API?  
   * *Ví dụ: "Chạy python app.py, sau đó truy cập localhost:8501"*  
5. **Project Structure:** Cây thư mục giải thích code nằm ở đâu.

### ---

### 

### 

### **MẸO CHO ĐỘI THI (BONUS TIPS)**

* **Test trên máy lạ:** Hãy thử clone repo của chính mình về một máy tính khác (hoặc xóa môi trường ảo cũ đi cài lại) để xem code có chạy được không trước khi nộp.  
* **Ghi lại thời gian:** Hãy ghi chú "Thời gian training dự kiến" (VD: 30 phút trên GPU T4) để giám khảo biết và chờ đợi.

---

