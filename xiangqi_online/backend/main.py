# file: backend/main.py
import asyncio
import websockets
from server import handler # Import cái hàm handler từ file server.py

async def main():
    # Chạy server WebSocket ở localhost (127.0.0.1) cổng 8765
    # Bất cứ ai kết nối vào 127.0.0.1:8765 sẽ được hàm handler xử lý
    async with websockets.serve(handler, "localhost", 8765):
        print("--- 🚀 WebSocket Server Cờ Tướng Đã Chạy ---")
        print("Đang lắng nghe tại: ws://localhost:8765")
        await asyncio.Future()  # Giữ server chạy mãi mãi

if __name__ == "__main__":
    asyncio.run(main())
