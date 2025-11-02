# 🚩 Game Cờ Tướng Online
## Bài tập lớn môn học Lập Trình Mạng

Đây là project game Cờ Tướng (Xiangqi) online cho 2 người chơi, được xây dựng cho môn học Lập Trình Mạng. Project sử dụng Python (WebSockets) cho backend và HTML/CSS/JavaScript cho frontend.

---

### 🛠️ Công nghệ sử dụng

* **Backend:** Python 3
* **Thư viện Python:** `websockets` (cho giao tiếp Client-Server)
* **Frontend:** HTML5, CSS3, JavaScript (ES6+)
* **Giao thức:** WebSocket (trên nền TCP)
* **Môi trường chạy:** VSCode + Extension "Live Server"

---

### 🎯 Tính năng chính

* **Logic Cờ Tướng:** Đã implement đầy đủ logic di chuyển chuẩn cho 7 loại quân (Tướng, Sĩ, Tượng, Xe, Pháo, Mã, Tốt).
* **Luật chơi nâng cao:**
    * Phát hiện nước đi **Chiếu Tướng** (Check).
    * Phát hiện nước đi **Chiếu Bí** (Checkmate) và thông báo người chiến thắng.
    * Ngăn chặn người chơi thực hiện nước đi **Tự chiếu** (tự sát).
* **Chơi Online 2 người:** Server có khả năng quản lý phòng chơi, tự động ghép 2 người chơi vào 1 ván.
* **Đồng bộ thời gian thực:** Nước đi của người này ngay lập tức được cập nhật trên màn hình của người kia.
* **Giao diện trực quan:** Hiển thị các nước đi hợp lệ (đã lọc "tự chiếu") bằng các chấm xanh khi người chơi chọn một quân.

---

### 🚀 Cài đặt và Chạy thử

Làm theo các bước sau để chạy project trên máy local.

#### 1. Cài đặt Backend (Python)

Mở terminal và di chuyển đến thư mục gốc `xiangqi_online`.


# 1. Tạo môi trường ảo (venv)
python -m venv backend/venv

# 2. Kích hoạt môi trường ảo
# Trên Windows:
backend\venv\Scripts\activate
# Trên macOS/Linux:
# source backend/venv/bin/activate

# 3. Cài đặt thư viện Websockets
pip install websockets

2. Sau khi kích hoạt venv và cài đặt xong, chạy server:
python backend/main.py

Nếu thành công, terminal sẽ hiển thị:
--- 🚀 WebSocket Server Cờ Tướng Đã Chạy ---
Đang lắng nghe tại: ws://localhost:8765

3. Chạy Client (Frontend):
Trong VSCode, click chuột phải vào file frontend/index.html .

Chọn "Open with Live Server".

Trình duyệt sẽ tự động mở (ví dụ: http://127.0.0.1:5500/frontend/index.html). Đây là Người chơi 1 (Red).

Tab này sẽ hiển thị: "Đang chờ người chơi khác..."

4. Bắt đầu chơi
Mở một cửa sổ ẩn danh (Incognito Window) (hoặc một trình duyệt khác).

Copy địa chỉ http://127.0.0.1:5500/frontend/index.html từ tab Người chơi 1.

Dán (paste) địa chỉ này vào cửa sổ ẩn danh. Đây là Người chơi 2 (Black).

Ngay khi tab thứ 2 kết nối, server sẽ tự động ghép cặp và game sẽ bắt đầu.

