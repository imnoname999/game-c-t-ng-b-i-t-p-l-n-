# file: backend/server.py (ĐÃ SỬA LỖI .closed "TRIỆT ĐỂ")

import asyncio
import json
import websockets
import uuid
from game_logic import Board, Piece, EMPTY

# --- Quản lý trạng thái server ---
WAITING_CLIENTS = set()
GAME_ROOMS = {}
CLIENT_ROOM_MAP = {}

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

async def broadcast_to_room(room_id, message_json):
    """Gửi một tin nhắn (JSON) cho cả 2 client trong phòng."""
    if room_id in GAME_ROOMS:
        message_str = json.dumps(message_json)
        clients = list(GAME_ROOMS[room_id]["clients"].keys())
        
        # ==================================
        # === SỬA LỖI 1 LÀ Ở ĐÂY ===
        # Bỏ check .closed, dùng gather + return_exceptions
        # để "nuốt" lỗi nếu client đã ngắt kết nối
        # ==================================
        tasks = [client.send(message_str) for client in clients]
        if tasks:
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
        "turn": "red"
    }
    GAME_ROOMS[room_id] = game_state
    
    CLIENT_ROOM_MAP[player1] = room_id
    CLIENT_ROOM_MAP[player2] = room_id

    print(f"Game started: Room {room_id} between {player1.remote_address} (Red) and {player2.remote_address} (Black)")

    board_state = serialize_board(board)
    
    msg_player1 = {
        "type": "start",
        "color": "red",
        "board": board_state,
        "turn": "red"
    }
    msg_player2 = {
        "type": "start",
        "color": "black",
        "board": board_state,
        "turn": "red"
    }

    await asyncio.gather(
        player1.send(json.dumps(msg_player1)),
        player2.send(json.dumps(msg_player2))
    )

async def handle_move(websocket, data):
    """Xử lý một tin nhắn 'move' từ client."""
    room_id = CLIENT_ROOM_MAP.get(websocket)
    if not room_id or room_id not in GAME_ROOMS:
        await websocket.send(json.dumps({"type": "error", "message": "Bạn không ở trong phòng game."}))
        return

    room = GAME_ROOMS[room_id]
    
    if room["turn"] is None:
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

        legal_moves = piece.get_legal_moves(board)
        
        if to_pos not in legal_moves:
            await websocket.send(json.dumps({"type": "error", "message": "Nước đi không hợp lệ (có thể do tự chiếu)."}))
            return
            
        board.move_piece(from_pos, to_pos)
        
        next_turn = "black" if my_color == "red" else "red"
        
        is_check = board.is_in_check(next_turn)
        is_checkmate = False
        
        if is_check:
            is_checkmate = board.is_checkmate(next_turn)

        if is_checkmate:
            room["turn"] = None 
            print(f"GAME OVER: {my_color} wins by checkmate!")
        else:
            room["turn"] = next_turn

        print(f"Room {room_id}: {my_color} move {from_pos} -> {to_pos}. Next: {room['turn']}. Check: {is_check}. Checkmate: {is_checkmate}")

        await broadcast_to_room(room_id, {
            "type": "game_update",
            "from": from_pos,
            "to": to_pos,
            "turn": room["turn"], 
            "is_check": is_check,
            "is_checkmate": is_checkmate,
            "winner": my_color if is_checkmate else None
        })

    except Exception as e:
        print(f"Error processing move: {e}")
        # Gửi lỗi về client
        try:
            await websocket.send(json.dumps({"type": "error", "message": "Có lỗi xảy ra (server)." + str(e)}))
        except:
            pass # Client cũng có thể đã ngắt kết nối

async def handle_get_moves(websocket, data):
    """Xử lý tin nhắn 'get_moves' từ client."""
    room_id = CLIENT_ROOM_MAP.get(websocket)
    if not room_id or room_id not in GAME_ROOMS:
        return

    room = GAME_ROOMS[room_id]
    board = room["board"]
    my_color = room["clients"].get(websocket)
    
    try:
        pos = tuple(data["pos"])
        piece = board.get_piece(pos[0], pos[1])

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
        other_player = None
        for client in room["clients"].keys():
            # ==================================
            # === SỬA LỖI 2 LÀ Ở ĐÂY ===
            # Bỏ check .closed
            # ==================================
            if client != websocket:
                other_player = client
        
        del GAME_ROOMS[room_id]
        if websocket in CLIENT_ROOM_MAP:
            del CLIENT_ROOM_MAP[websocket]
        
        if other_player:
            # ==================================
            # === VÀ THÊM TRY/EXCEPT Ở ĐÂY ===
            # ==================================
            try:
                await other_player.send(json.dumps({"type": "opponent_left"}))
                if other_player in CLIENT_ROOM_MAP:
                    del CLIENT_ROOM_MAP[other_player]
            except:
                print("Broadcast 'opponent_left' failed. Other player likely disconnected.")
        
async def handler(websocket):
    """Hàm xử lý chính cho mỗi kết nối WebSocket."""
    print(f"Client connected: {websocket.remote_address}")
    
    WAITING_CLIENTS.add(websocket)

    if len(WAITING_CLIENTS) >= 2:
        player1 = WAITING_CLIENTS.pop()
        player2 = WAITING_CLIENTS.pop()
        
        asyncio.create_task(start_game(player1, player2))
    else:
        await websocket.send(json.dumps({"type": "wait", "message": "Đang chờ người chơi khác..."}))

    try:
        async for message in websocket:
            data = json.loads(message)
            
            if data["type"] == "move":
                await handle_move(websocket, data)
            elif data["type"] == "get_moves":
                await handle_get_moves(websocket, data)
            
    except websockets.exceptions.ConnectionClosed:
        print(f"Connection closed for {websocket.remote_address}")
    finally:
        await cleanup(websocket)