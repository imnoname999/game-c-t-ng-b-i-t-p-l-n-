## ⚙️ Hướng dẫn Cài đặt

### 1. Backend (Python)

1.  Di chuyển vào thư mục `backend`: cd backend

2.  Tạo môi trường ảo (nếu bạn chưa có thư mục `venv`): python -m venv venv

3.  Kích hoạt môi trường ảo:
    * **Trên Windows (CMD/PowerShell):** .\venv\Scripts\activate

    * **Trên macOS/Linux:** source venv/bin/activate

4.  Cài đặt thư viện `websockets` (đây là thư viện duy nhất cần cài):
    pip install websockets

### 2. Frontend (HTML/JS)
* **Không cần cài đặt!** Ní chỉ cần mở file `frontend/index.html` bằng trình duyệt.

## 🏁 Hướng dẫn Sử dụng (Chạy game)
- Để kiểm tra game, ní cần chạy **1 Server** và **2 Client** (vì game tự động ghép 2 người).

### 1. Khởi động Server 🚀
1.  Mở Terminal (hoặc CMD/PowerShell).
2.  Đảm bảo ní đã ở trong thư mục `backend/` và đã **kích hoạt môi trường ảo** (xem bước 1.3 ở trên).
3.  Chạy file `main.py` để khởi động server:
    python main.py

4.  Nếu thành công, server sẽ hiển thị:
    --- 🚀 WebSocket Server Cờ Tướng Đã Chạy ---
    Đang lắng nghe tại: ws://localhost:8765

### 2. Bắt đầu chơi (2 Client) 🎮
1.  **Client 1:** Mở file `frontend/index.html` bằng trình duyệt (ví dụ: Chrome).
    * Trang web sẽ hiển thị: "**Đang chờ người chơi khác...**"

2.  **Client 2:** Mở file `frontend/index.html` trong một **tab mới** (hoặc một cửa sổ trình duyệt mới).

3.  Ngay khi Client 2 kết nối, server sẽ tự động ghép cặp cả hai.
    * Ván cờ bắt đầu! Một người sẽ là Đỏ, một người là Đen, và đồng hồ bắt đầu đếm ngược.