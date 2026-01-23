# Regex Parsing Logic for NASA HTTP Logs

Tài liệu này giải thích chi tiết logic Regex được sử dụng để xử lý log NASA (Common Log Format). Quy trình gồm 2 bước: tách dòng log thô và phân tích chuỗi Request.

## 1. Giải thích Regex Pattern

### Giai đoạn 1: Parse dòng Log (Log Extraction)
Mục tiêu là trích xuất 5 trường thông tin cơ bản từ một dòng log text.

**Regex Pattern:**
`^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"([^"]*)"\s+(\d{3})\s+(\S+)\s*$`

**Phân tích chi tiết:**
1.  `^(\S+)`: **Host/IP**. Bắt đầu dòng, lấy chuỗi ký tự liền mạch (không khoảng trắng).
2.  `\s+\S+\s+\S+\s+`: **Bỏ qua Ident/Auth**. Khớp với khoảng trắng và 2 dấu gạch ngang (`- -`) thường thấy trong chuẩn CLF.
3.  `\[([^\]]+)\]`: **Timestamp**. Lấy toàn bộ nội dung nằm trong cặp ngoặc vuông `[]`.
    *   Ví dụ: `01/Jul/1995:00:00:01 -0400`
4.  `"([^"]*)"`: **Request String**. Lấy toàn bộ nội dung trong cặp ngoặc kép `""`.
    *   Ví dụ: `GET /history/apollo/ HTTP/1.0`
5.  `(\d{3})`: **Status Code**. Lấy chính xác 3 chữ số (ví dụ: `200`, `404`).
6.  `(\S+)`: **Bytes**. Lấy chuỗi ký tự cuối cùng (thường là số bytes hoặc dấu `-` nếu không có dữ liệu).

---

### Giai đoạn 2: Tách Request (Request Parsing)
Mục tiêu là tách chuỗi Request (lấy được ở Giai đoạn 1) thành Method, URL và Protocol.

**Regex Pattern:**
`^(\S+)\s+(\S+)(?:\s+(\S+))?$`

**Phân tích chi tiết:**
1.  `^(\S+)`: **Method**. Từ đầu tiên (ví dụ: `GET`, `POST`).
2.  `\s+(\S+)`: **URL/Path**. Chuỗi tiếp theo (ví dụ: `/images/logo.gif`). Đây là thành phần quan trọng cần giữ lại ở Log-level.
3.  `(?:\s+(\S+))?$`: **Protocol** (Optional). Phần cuối cùng (ví dụ: `HTTP/1.0`). Nhóm này có thể không tồn tại trong các request đơn giản (HTTP/0.9).

---

## 2. Python Script Implementation

Dưới đây là cách hai pattern trên được áp dụng trong code Python (sử dụng `re` module với Named Groups để dễ quản lý):

```python
import re

# 1. LOG_RE: Dùng để tách dòng log
LOG_RE = re.compile(
    r'^(?P<host>\S+)\s+'          # Host
    r'\S+\s+\S+\s+'               # Skip ident/auth
    r'\[(?P<ts>[^\]]+)\]\s+'      # Timestamp
    r'"(?P<request>[^"]*)"\s+'    # Full Request
    r'(?P<status>\d{3})\s+'       # Status
    r'(?P<bytes>\S+)\s*$'         # Bytes
)

# 2. REQ_RE: Dùng để tách chi tiết Request
REQ_RE = re.compile(
    r'^(?P<method>\S+)\s+'        # Method
    r'(?P<url>\S+)'               # URL (Path)
    r'(?:\s+(?P<protocol>\S+))?$' # Protocol (Optional)
)
```
