# file: backend/server.py
import asyncio
import json
import websockets
import uuid
import time
import os
import ast # Thư viện này dùng cho hàm format history
from datetime import datetime # Thư viện này dùng cho hàm format history
from game_logic import Board, Piece, EMPTY

# --- Quản lý trạng thái server ---
WAITING_CLIENTS = set()
GAME_ROOMS = {}
CLIENT_ROOM_MAP = {}

# === HẰNG SỐ TIMER ===
TOTAL_TIME_PER_PLAYER = 300 # 300 giây = 5 phút
TIMER_TICK_RATE = 1 # Cập nhật (trừ) 1 giây mỗi lần

# === HẰNG SỐ HISTORY ===
HISTORY_DIR = "backend/history"


def serialize_board(board):
    """Chuyển đổi object Board thành một cấu trúc JSON đơn giản."""
    grid_simple = []
    for r in range(board.ROWS):
        row_simple = []
        for c in range(board.COLS):
            piece = board.get_piece(r, c)
            if piece:
                row_simple.append(f"{piece.color[0].upper()}_{piece.name}")
            else:
                row_simple.append(EMPTY)
        grid_simple.append(row_simple)
    return grid_simple

# ==========================================================
# === SỬA ĐỔI 2.1: HÀM MỚI ĐỂ LẤY ID FILE TIẾP THEO ===
# ==========================================================
def get_next_history_id():
    """
    Quét thư mục HISTORY_DIR, tìm số lớn nhất (vd: "25.txt")
    và trả về số tiếp theo (vd: 26).
    """
    if not os.path.exists(HISTORY_DIR):
        return 1 # Nếu thư mục chưa tồn tại, bắt đầu từ 1
    
    max_id = 0
    try:
        files = os.listdir(HISTORY_DIR)
        for filename in files:
            # Chỉ xét các file .txt
            if filename.endswith(".txt"):
                try:
                    # Tách tên file (vd: "25.txt" -> "25")
                    file_id = int(os.path.splitext(filename)[0])
                    if file_id > max_id:
                        max_id = file_id
                except ValueError:
                    # Bỏ qua các file không phải là số (vd: file UUID cũ)
                    pass 
    except Exception as e:
        print(f"[History] Lỗi khi quét thư mục history: {e}")
        # Nếu lỗi, trả về 1 tên ngẫu nhiên để tránh ghi đè
        return f"error_{uuid.uuid4()}" 
        
    return max_id + 1
# ==========================================================

def save_game_history(room_id, room_data, result):
    """Lưu thông tin ván cờ (CHỈ LƯU file .txt)."""
    if not os.path.exists(HISTORY_DIR):
        try:
            os.makedirs(HISTORY_DIR)
        except OSError as e:
            print(f"[History] Không thể tạo thư mục {HISTORY_DIR}: {e}")
            return
    
    # --- 1. Lấy thông tin (như cũ) ---
    player_red_addr = "Unknown"
    player_black_addr = "Unknown"
    try:
        for client, color in room_data.get("clients", {}).items():
            if color == "red":
                player_red_addr = str(client.remote_address)
            elif color == "black":
                player_black_addr = str(client.remote_address)
    except Exception:
        pass # Bỏ qua nếu client đã ngắt kết nối

    history_data = {
        "room_id": room_id,
        "start_time": room_data.get("start_time", time.time()),
        "end_time": time.time(),
        "player_red": player_red_addr,
        "player_black": player_black_addr,
        "result": result,
        "moves": room_data.get("moves_history", [])
    }

    # --- 2. (ĐÃ XÓA) Phần lưu file .json ---

    # --- 3. Chỉ Lưu file .txt ---
    try:
        human_readable_text = format_history_to_text(history_data)

        # ============================================================
        # === SỬA ĐỔI 2.2: Lấy ID tuần tự cho tên file ===
        # ============================================================
        # Thay vì dùng room_id (UUID), ta dùng số thứ tự
        new_file_id = get_next_history_id()
        txt_filepath = os.path.join(HISTORY_DIR, f"{new_file_id}.txt")
        # ============================================================

        with open(txt_filepath, 'w', encoding='utf-8') as f:
            f.write(human_readable_text)
        
        print(f"[History] Đã lưu bản đọc: {txt_filepath}")
    
    except Exception as e:
        print(f"[History] Lỗi khi lưu file TXT {room_id}: {e}")


# ===============================================
# === CÁC HÀM ĐỌC LỊCH SỬ (Giữ nguyên) ===
# ===============================================
def _parse_player_addr(addr_str):
    if addr_str == "Unknown" or not addr_str:
        return "Không rõ"
    try:
        # ast.literal_eval an toàn hơn eval()
        addr_tuple = ast.literal_eval(addr_str)
        ip = addr_tuple[0]
        port = addr_tuple[1]
        return f"IP ({ip}), cổng {port}"
    except Exception:
        return addr_str

def _format_result(result_dict):
    winner_map = {'red': 'Đỏ', 'black': 'Đen'}

    reason_map = {
        'opponent_left': 'đối thủ rời trận',
        'checkmate': 'chiếu bí',
        'timeout': 'hết giờ',
        'stalemate': 'ép đối thủ vào thế "Bí"',
        'resign': 'đầu hàng'
    }

    winner_color = result_dict.get('winner')
    reason_key = result_dict.get('reason')

    if not winner_color or not reason_key:
        return "Kết quả: Không rõ"

    winner_text = winner_map.get(winner_color, winner_color.capitalize())
    reason_text = reason_map.get(reason_key, reason_key)

    return f"Kết quả:  🏆  {winner_text} thắng (lý do: {reason_text})"


def format_history_to_text(history_data):
    """Hàm này có thể dùng nếu ní muốn mở rộng app, đọc lại lịch sử."""
    output_lines = []
    try:
        output_lines.append("  🧩  Lịch sử ván đấu")
        output_lines.append("-----------------------------------")
        output_lines.append(f"Mã phòng: {history_data.get('room_id', 'N/A')}")

        start_dt = datetime.fromtimestamp(history_data.get('start_time', 0))
        end_dt = datetime.fromtimestamp(history_data.get('end_time', 0))

        output_lines.append(f"Thời gian bắt đầu: {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append(f"Thời gian kết thúc: {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")

        output_lines.append(f"Người chơi bên Đỏ: {_parse_player_addr(history_data.get('player_red', 'Unknown'))}")
        output_lines.append(f"Người chơi bên Đen: {_parse_player_addr(history_data.get('player_black', 'Unknown'))}")

        output_lines.append(_format_result(history_data.get('result', {})))

        output_lines.append("\nCác nước đi:")
        moves = history_data.get('moves', [])
        if not moves:
            output_lines.append("(Không có nước đi nào được ghi lại)")

        color_map = {'red': 'Đỏ', 'black': 'Đen'}
        
        # ================================================
        # === SỬA ĐỔI 1: BỎ EMOJI SỐ ===
        # ================================================
        # (Đã xóa dòng number_emojis)
        
        for i, move in enumerate(moves, 1):
            color_text = color_map.get(move.get('color'), 'N/A')
            from_pos = tuple(move.get('from', ('?', '?')))
            to_pos = tuple(move.get('to', ('?', '?')))

            # Luôn dùng f"{i}." (vd: "1.", "2.", "11.")
            prefix = f"{i}."
            output_lines.append(f"{prefix} {color_text} đi từ {from_pos} → {to_pos}")
        # ================================================

    except Exception as e:
        return f"Lỗi khi định dạng lịch sử: {e}"

    return "\n".join(output_lines)
# ===============================================
# ===============================================

# === TÁC VỤ ĐẾM NGƯỢC (Giữ nguyên) ===
async def game_timer_task(room_id):
    """Chạy song song để đếm ngược thời gian."""
    if room_id not in GAME_ROOMS:
        return

    room = GAME_ROOMS[room_id]
    print(f"[Timer Room {room_id}]: Task Bắt đầu.")

    try:
        while room_id in GAME_ROOMS:
            await asyncio.sleep(TIMER_TICK_RATE)

            # Nếu game đã dừng (do chiếu bí,...) thì dừng task timer
            if room["turn"] is None:
                break

            time_key = f"{room['turn']}_time"
            room[time_key] -= TIMER_TICK_RATE
            room["last_update_time"] = time.time()

            is_timeout = False
            winner = None

            if room[time_key] <= 0:
                is_timeout = True
                room[time_key] = 0
                loser = room["turn"]
                winner = "black" if loser == "red" else "red"
                room["turn"] = None # Dừng game
                print(f"[Timer Room {room_id}]: Hết giờ! {winner} thắng.")

                # Lưu lịch sử
                save_game_history(
                    room_id, room, {"winner": winner, "reason": "timeout"})

                # Gửi tin nhắn kết thúc riêng
                await broadcast_to_room(room_id, {
                    "type": "game_over",
                    "winner": winner,
                    "reason": "timeout"
                })

            # Chỉ gửi timer_update nếu game CHƯA hết giờ
            # (Gửi mỗi 1 giây để client đồng bộ)
            if not is_timeout and (room[time_key] % 1 == 0):
                await broadcast_to_room(room_id, {
                    "type": "timer_update",
                    "red_time": room["red_time"],
                    "black_time": room["black_time"],
                    "turn": room["turn"]
                })

            if is_timeout:
                break # Dừng vòng lặp

    except Exception as e:
        print(f"[Timer Room {room_id}]: Lỗi {e}")
    finally:
        print(f"[Timer Room {room_id}]: Task Kết thúc.")


async def broadcast_to_room(room_id, message_json):
    """Gửi một tin nhắn (JSON) cho cả 2 client trong phòng."""
    if room_id in GAME_ROOMS:
        message_str = json.dumps(message_json)
        clients = list(GAME_ROOMS[room_id]["clients"].keys())

        # Tạo task gửi cho từng client
        tasks = [client.send(message_str) for client in clients]
        if tasks:
            # Thực thi song song và bỏ qua lỗi nếu 1 client đã disconnect
            await asyncio.gather(*tasks, return_exceptions=True)


async def start_game(player1, player2):
    """Khởi tạo một ván game mới cho 2 client."""
    room_id = str(uuid.uuid4())
    board = Board()

    game_state = {
        "board": board,
        "clients": {
            player1: "red",
            player2: "black"
        },
        "turn": "red",
        "red_time": TOTAL_TIME_PER_PLAYER,
        "black_time": TOTAL_TIME_PER_PLAYER,
        "last_update_time": time.time(),
        "timer_task": None,
        "moves_history": [],
        "start_time": time.time()
    }

    GAME_ROOMS[room_id] = game_state
    CLIENT_ROOM_MAP[player1] = room_id
    CLIENT_ROOM_MAP[player2] = room_id

    print(f"Game started: Room {room_id} between {player1.remote_address} (Red) and {player2.remote_address} (Black)")

    board_state = serialize_board(board)

    # Tin nhắn chung
    common_msg_data = {
        "board": board_state,
        "turn": "red",
        "red_time": TOTAL_TIME_PER_PLAYER,
        "black_time": TOTAL_TIME_PER_PLAYER
    }

    # Gửi tin nhắn riêng cho mỗi người
    msg_player1 = {"type": "start", "color": "red", **common_msg_data}
    msg_player2 = {"type": "start", "color": "black", **common_msg_data}

    await asyncio.gather(
        player1.send(json.dumps(msg_player1)),
        player2.send(json.dumps(msg_player2))
    )

    # Bắt đầu chạy Task đếm giờ
    game_state["timer_task"] = asyncio.create_task(game_timer_task(room_id))


# === HÀM handle_move (Giữ nguyên) ===
async def handle_move(websocket, data):
    """Xử lý một tin nhắn 'move' từ client."""
    room_id = CLIENT_ROOM_MAP.get(websocket)
    if not room_id or room_id not in GAME_ROOMS:
        await websocket.send(json.dumps({"type": "error", "message": "Bạn không ở trong phòng game."}))
        return

    room = GAME_ROOMS[room_id]

    # Nếu game đã kết thúc (turn = None) thì không xử lý
    if room["turn"] is None:
        await websocket.send(json.dumps({"type": "error", "message": "Game đã kết thúc."}))
        return

    board = room["board"]
    my_color = room["clients"].get(websocket)

    if room["turn"] != my_color:
        await websocket.send(json.dumps({"type": "error", "message": "Chưa tới lượt của bạn."}))
        return

    try:
        from_pos = tuple(data["from"])
        to_pos = tuple(data["to"])

        piece = board.get_piece(from_pos[0], from_pos[1])

        if piece is None or piece.color != my_color:
            await websocket.send(json.dumps({"type": "error", "message": "Đây không phải quân của bạn."}))
            return

        # Kiểm tra nước đi hợp lệ (đã lọc tự chiếu)
        legal_moves = piece.get_legal_moves(board)

        if to_pos not in legal_moves:
            await websocket.send(json.dumps({"type": "error", "message": "Nước đi không hợp lệ (có thể do tự chiếu)."}))
            return

        # OK, nước đi hợp lệ
        board.move_piece(from_pos, to_pos)

        # Lưu vào lịch sử
        room["moves_history"].append(
            {"from": from_pos, "to": to_pos, "color": my_color, "time": time.time()})

        next_turn = "black" if my_color == "red" else "red"

        # Kiểm tra trạng thái sau nước đi
        is_check = board.is_in_check(next_turn)
        is_checkmate = False
        is_stalemate = False
        winner = None
        game_over_reason = None # Biến mới

        if is_check:
            is_checkmate = board.is_checkmate(next_turn)
        else:
            # Nếu không chiếu, mới kiểm tra "Bí" (Stalemate)
            is_stalemate = board.is_stalemate(next_turn)

        if is_checkmate:
            room["turn"] = None
            winner = my_color
            game_over_reason = "checkmate"
            print(f"GAME OVER: {my_color} wins by CHECKMATE!")
            save_game_history(room_id, room, {"winner": winner, "reason": game_over_reason})

        elif is_stalemate:
            room["turn"] = None
            winner = my_color # Thắng do ép đối thủ vào thế "Bí"
            game_over_reason = "stalemate"
            print(f"GAME OVER: {my_color} wins by STALEMATE!")
            save_game_history(room_id, room, {"winner": winner, "reason": game_over_reason})

        else:
            # Game tiếp tục
            room["turn"] = next_turn
            room["last_update_time"] = time.time()

        print(f"Room {room_id}: {my_color} move {from_pos} -> {to_pos}. Next: {room['turn']}. Check: {is_check}. Checkmate: {is_checkmate}. Stalemate: {is_stalemate}")

        if game_over_reason:
            # Gửi tin nhắn KẾT THÚC GAME
            await broadcast_to_room(room_id, {
                "type": "game_over",
                "winner": winner,
                "reason": game_over_reason,
                # Gửi kèm nước đi cuối cùng
                "from": from_pos,
                "to": to_pos
            })
        else:
            # Gửi tin nhắn CẬP NHẬT GAME (như cũ)
            await broadcast_to_room(room_id, {
                "type": "game_update",
                "from": from_pos,
                "to": to_pos,
                "turn": room["turn"],
                "is_check": is_check,
                "red_time": room["red_time"],
                "black_time": room["black_time"]
            })

    except Exception as e:
        print(f"Error processing move: {e}")
        try:
            await websocket.send(json.dumps({"type": "error", "message": "Có lỗi xảy ra (server)." + str(e)}))
        except:
            pass # Client có thể đã ngắt kết nối


# *** Hàm mới `handle_resign` (Giữ nguyên) ***
async def handle_resign(websocket):
    """Xử lý khi client gửi tin nhắn 'resign'."""
    room_id = CLIENT_ROOM_MAP.get(websocket)
    if not room_id or room_id not in GAME_ROOMS:
        return # Không báo lỗi, chỉ lờ đi

    room = GAME_ROOMS[room_id]

    # Chỉ xử lý nếu game đang diễn ra
    if room["turn"] is None:
        return

    try:
        loser_color = room["clients"].get(websocket)
        if not loser_color:
            return # Không tìm thấy client này

        winner_color = "black" if loser_color == "red" else "red"

        # Dừng game
        room["turn"] = None

        print(f"[Game Room {room_id}]: {loser_color} đã đầu hàng. {winner_color} thắng.")

        # Lưu lịch sử
        save_game_history(
            room_id, room, {"winner": winner_color, "reason": "resign"})

        # Gửi tin nhắn kết thúc cho cả 2
        await broadcast_to_room(room_id, {
            "type": "game_over",
            "winner": winner_color,
            "reason": "resign"
        })

    except Exception as e:
        print(f"Lỗi khi xử lý resign: {e}")
# *****************************************

async def handle_get_moves(websocket, data):
    """Xử lý tin nhắn 'get_moves' từ client."""
    room_id = CLIENT_ROOM_MAP.get(websocket)
    if not room_id or room_id not in GAME_ROOMS:
        return # Không cần báo lỗi

    room = GAME_ROOMS[room_id]
    board = room["board"]
    my_color = room["clients"].get(websocket)

    try:
        pos = tuple(data["pos"])
        piece = board.get_piece(pos[0], pos[1])

        # Chỉ gửi nước đi nếu đúng là quân của mình
        if piece and piece.color == my_color:
            legal_moves = piece.get_legal_moves(board)
            await websocket.send(json.dumps({
                "type": "valid_moves",
                "moves": legal_moves
            }))
    except Exception as e:
        print(f"Error getting moves: {e}")


async def cleanup(websocket):
    """Dọn dẹp khi client ngắt kết nối."""
    if websocket in WAITING_CLIENTS:
        WAITING_CLIENTS.remove(websocket)
        print(f"Client waiting {websocket.remote_address} disconnected.")
        return

    room_id = CLIENT_ROOM_MAP.get(websocket)
    if room_id and room_id in GAME_ROOMS:
        print(f"Client {websocket.remote_address} in room {room_id} disconnected.")
        room = GAME_ROOMS[room_id]

        # Nếu game đang diễn ra thì xử lý
        if room.get("turn") is not None:
            try:
                loser_color = room["clients"].get(websocket)
                if loser_color:
                    winner_color = "black" if loser_color == "red" else "red"
                    save_game_history(
                        room_id, room, {"winner": winner_color, "reason": "opponent_left"})
            except Exception as e:
                print(f"[History] Lỗi khi lưu game {room_id} do cleanup: {e}")

        # Dừng task timer (nếu có)
        if room.get("timer_task"):
            room["timer_task"].cancel()

        other_player = None
        for client in room["clients"].keys():
            if client != websocket:
                other_player = client

        # Xóa phòng
        del GAME_ROOMS[room_id]
        if websocket in CLIENT_ROOM_MAP:
            del CLIENT_ROOM_MAP[websocket]

        if other_player:
            try:
                # Gửi "game_over" cho người chơi còn lại
                loser_color = room["clients"].get(websocket, "Unknown")
                winner_color = "black" if loser_color == "red" else "red"

                await other_player.send(json.dumps({
                    "type": "game_over",
                    "winner": winner_color,
                    "reason": "opponent_left"
                }))

                if other_player in CLIENT_ROOM_MAP:
                    del CLIENT_ROOM_MAP[other_player]
            except:
                print("Broadcast 'game_over' (opponent_left) failed.")


async def handler(websocket):
    """Hàm xử lý chính cho mỗi kết nối WebSocket."""
    print(f"Client connected: {websocket.remote_address}")

    # Thêm client vào hàng chờ
    WAITING_CLIENTS.add(websocket)

    # Nếu đủ 2 người, bắt đầu game
    if len(WAITING_CLIENTS) >= 2:
        player1 = WAITING_CLIENTS.pop()
        player2 = WAITING_CLIENTS.pop()
        asyncio.create_task(start_game(player1, player2))
    else:
        # Nếu chưa đủ, gửi tin nhắn chờ
        await websocket.send(json.dumps({"type": "wait", "message": "Đang chờ người chơi khác..."}))

    try:
        # Vòng lặp lắng nghe tin nhắn từ client
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "move":
                await handle_move(websocket, data)
            elif data["type"] == "get_moves":
                await handle_get_moves(websocket, data)
            elif data["type"] == "resign":
                await handle_resign(websocket)

    except websockets.exceptions.ConnectionClosed:
        print(f"Connection closed for {websocket.remote_address}")
    finally:
        # Dọn dẹp khi client ngắt kết nối
        await cleanup(websocket)
