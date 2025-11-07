# file: backend/game_logic.py

# Hằng số
ROWS = 10
COLS = 9
EMPTY = None

# --- CLASS CHA (Giống như trước) ---

class Piece:
    """Class cha cho tất cả các quân cờ."""
    def __init__(self, color, position):
        self.color = color
        self.position = position
        self.name = self.__class__.__name__

    def __repr__(self):
        names_unicode = {
            'General': ' tướng', 'Advisor': ' sĩ', 'Elephant': ' tượng',
            'Rook': ' xe', 'Cannon': ' pháo', 'Knight': ' mã', 'Pawn': ' tốt'
        }
        color_prefix = 'B' if self.color == 'black' else 'R'
        return f"{color_prefix}{names_unicode.get(self.name, self.name)}@({self.position[0]},{self.position[1]})"

    def is_valid_move(self, board, new_pos):
        return new_pos in self.get_valid_moves(board)

    def get_valid_moves(self, board):
        """Lấy các nước đi CƠ BẢN (chưa lọc tự chiếu)"""
        raise NotImplementedError("Phải override trong class con")

    # ==================================
    # === HÀM NÀY PHẢI NẰM Ở ĐÂY ===
    # ==================================
    def get_legal_moves(self, board):
        """
        Lấy các nước đi HỢP LỆ (đã lọc các nước 'tự chiếu').
        """
        legal_moves = []
        # Lấy các nước đi cơ bản (chưa lọc)
        pseudo_legal_moves = self.get_valid_moves(board)
        
        for move in pseudo_legal_moves:
            # Dùng 'test_move' để mô phỏng
            for _ in board.test_move(self.position, move):
                # Sau khi đi thử, kiểm tra xem Tướng của mình có bị chiếu không
                if not board.is_in_check(self.color):
                    # Nếu không bị chiếu -> đây là nước đi hợp lệ
                    legal_moves.append(move)
                    
        return legal_moves

    def is_enemy(self, piece):
        return piece is not EMPTY and piece.color != self.color

    def is_friendly(self, piece):
        return piece is not EMPTY and piece.color == self.color

    def _is_in_palace(self, pos):
        r, c = pos
        if not (3 <= c <= 5):
            return False
        if self.color == 'red':
            return 7 <= r <= 9
        else: # 'black'
            return 0 <= r <= 2

# --- CLASS BÀN CỜ (ĐÃ CẬP NHẬT SETUP) ---

class Board:
    """Class đại diện cho bàn cờ."""
    def __init__(self):
        self.grid = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        self.setup_pieces()
        self.red_general_pos = (9, 4)
        self.black_general_pos = (0, 4)
        self.ROWS = ROWS
        self.COLS = COLS

    def setup_pieces(self):
        # ... (Phần setup_pieces giữ nguyên, tui ẩn đi cho đỡ dài) ...
        # --- Đặt quân Đen (Black) ---
        self.grid[0][0] = Rook('black', (0, 0))
        self.grid[0][1] = Knight('black', (0, 1))
        self.grid[0][2] = Elephant('black', (0, 2))
        self.grid[0][3] = Advisor('black', (0, 3))
        self.grid[0][4] = General('black', (0, 4))
        self.grid[0][5] = Advisor('black', (0, 5))
        self.grid[0][6] = Elephant('black', (0, 6))
        self.grid[0][7] = Knight('black', (0, 7))
        self.grid[0][8] = Rook('black', (0, 8))
        self.grid[2][1] = Cannon('black', (2, 1))
        self.grid[2][7] = Cannon('black', (2, 7))
        self.grid[3][0] = Pawn('black', (3, 0))
        self.grid[3][2] = Pawn('black', (3, 2))
        self.grid[3][4] = Pawn('black', (3, 4))
        self.grid[3][6] = Pawn('black', (3, 6))
        self.grid[3][8] = Pawn('black', (3, 8))
        # --- Đặt quân Đỏ (Red) ---
        self.grid[9][0] = Rook('red', (9, 0))
        self.grid[9][1] = Knight('red', (9, 1))
        self.grid[9][2] = Elephant('red', (9, 2))
        self.grid[9][3] = Advisor('red', (9, 3))
        self.grid[9][4] = General('red', (9, 4))
        self.grid[9][5] = Advisor('red', (9, 5))
        self.grid[9][6] = Elephant('red', (9, 6))
        self.grid[9][7] = Knight('red', (9, 7))
        self.grid[9][8] = Rook('red', (9, 8))
        self.grid[7][1] = Cannon('red', (7, 1))
        self.grid[7][7] = Cannon('red', (7, 7))
        self.grid[6][0] = Pawn('red', (6, 0))
        self.grid[6][2] = Pawn('red', (6, 2))
        self.grid[6][4] = Pawn('red', (6, 4))
        self.grid[6][6] = Pawn('red', (6, 6))
        self.grid[6][8] = Pawn('red', (6, 8))

    def get_piece(self, row, col):
        if 0 <= row < ROWS and 0 <= col < COLS:
            return self.grid[row][col]
        return None

    def move_piece(self, from_pos, to_pos):
        r_from, c_from = from_pos
        r_to, c_to = to_pos
        piece = self.get_piece(r_from, c_from)
        if piece:
            captured_piece = self.get_piece(r_to, c_to)
            if isinstance(piece, General):
                if piece.color == 'red':
                    self.red_general_pos = to_pos
                else:
                    self.black_general_pos = to_pos
            self.grid[r_to][c_to] = piece
            self.grid[r_from][c_from] = EMPTY
            piece.position = to_pos
            return captured_piece
        return None

    def is_generals_facing(self):
        r_red, c_red = self.red_general_pos
        r_black, c_black = self.black_general_pos
        if c_red != c_black:
            return False
        for r in range(r_black + 1, r_red):
            if self.get_piece(r, c_red) is not EMPTY:
                return False
        return True

    def is_in_check(self, color):
        """Kiểm tra xem Tướng của phe 'color' có đang bị chiếu không."""
        if color == 'red':
            my_general_pos = self.red_general_pos
            enemy_color = 'black'
        else:
            my_general_pos = self.black_general_pos
            enemy_color = 'red'
            
        enemy_pieces = []
        for r in range(self.ROWS):
            for c in range(self.COLS):
                piece = self.get_piece(r, c)
                if piece and piece.color == enemy_color:
                    enemy_pieces.append(piece)
        
        for piece in enemy_pieces:
            moves = piece.get_valid_moves(self)
            if my_general_pos in moves:
                return True 
                
        if self.is_generals_facing():
             return True
             
        return False

    def test_move(self, from_pos, to_pos):
        """'Mô phỏng' một nước đi."""
        r_from, c_from = from_pos
        r_to, c_to = to_pos
        piece_to_move = self.get_piece(r_from, c_from)
        if not piece_to_move:
            yield
            return
            
        captured_piece = self.get_piece(r_to, c_to)
        original_pos = piece_to_move.position
        old_red_gen_pos = self.red_general_pos
        old_black_gen_pos = self.black_general_pos

        self.grid[r_to][c_to] = piece_to_move
        self.grid[r_from][c_from] = EMPTY
        piece_to_move.position = to_pos
        
        if isinstance(piece_to_move, General):
            if piece_to_move.color == 'red':
                self.red_general_pos = to_pos
            else:
                self.black_general_pos = to_pos
        yield
        
        self.grid[r_from][c_from] = piece_to_move
        self.grid[r_to][c_to] = captured_piece
        piece_to_move.position = original_pos
        self.red_general_pos = old_red_gen_pos
        self.black_general_pos = old_black_gen_pos

    def is_checkmate(self, color):
        """Kiểm tra xem phe 'color' có bị Chiếu Bí không."""
        if not self.is_in_check(color):
            return False
            
        my_pieces = []
        for r in range(self.ROWS):
            for c in range(self.COLS):
                piece = self.get_piece(r, c)
                if piece and piece.color == color:
                    my_pieces.append(piece)

        for piece in my_pieces:
            # GIỜ SẼ CHẠY ĐÚNG VÌ MỌI QUÂN CỜ ĐỀU CÓ HÀM NÀY
            if len(piece.get_legal_moves(self)) > 0:
                return False
                
        return True

# --- LOGIC CÁC QUÂN CỜ (FULL) ---

class Rook(Piece):
    def get_valid_moves(self, board):
        moves = []
        r, c = self.position
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while 0 <= nr < ROWS and 0 <= nc < COLS:
                target_piece = board.get_piece(nr, nc)
                if target_piece is EMPTY:
                    moves.append((nr, nc))
                elif self.is_enemy(target_piece):
                    moves.append((nr, nc))
                    break
                else: 
                    break
                nr, nc = nr + dr, nc + dc
        return moves
    
    # === HÀM GET_LEGAL_MOVES ĐÃ BỊ XÓA KHỎI ĐÂY ===

class Knight(Piece):
    def get_valid_moves(self, board):
        moves = []
        r, c = self.position
        potential_moves = [
            ((-1, 0), (-2, 1)), ((-1, 0), (-2, -1)),
            ((1, 0), (2, 1)), ((1, 0), (2, -1)),
            ((0, -1), (-1, -2)), ((0, -1), (1, -2)),
            ((0, 1), (-1, 2)), ((0, 1), (1, 2))
        ]
        
        for (dr_leg, dc_leg), (dr_target, dc_target) in potential_moves:
            leg_r, leg_c = r + dr_leg, c + dc_leg
            target_r, target_c = r + dr_target, c + dc_target
            
            if not (0 <= target_r < ROWS and 0 <= target_c < COLS):
                continue
            
            leg_piece = board.get_piece(leg_r, leg_c)
            if leg_piece is not EMPTY:
                continue 
            
            target_piece = board.get_piece(target_r, target_c)
            if target_piece is EMPTY or self.is_enemy(target_piece):
                moves.append((target_r, target_c))
                
        return moves

class General(Piece):
    def get_valid_moves(self, board):
        moves = []
        r, c = self.position
        potential_moves = [(r+1, c), (r-1, c), (r, c+1), (r, c-1)]
        
        enemy_gen_pos = board.black_general_pos if self.color == 'red' else board.red_general_pos

        for nr, nc in potential_moves:
            if not self._is_in_palace((nr, nc)):
                continue
            target_piece = board.get_piece(nr, nc)
            if self.is_friendly(target_piece):
                continue
                
            if nc != enemy_gen_pos[1]:
                moves.append((nr, nc))
            else:
                is_safe = False
                min_r, max_r = sorted((nr, enemy_gen_pos[0]))
                for check_r in range(min_r + 1, max_r):
                    if board.get_piece(check_r, nc) is not EMPTY:
                        is_safe = True 
                        break
                if is_safe:
                    moves.append((nr, nc))
                    
        return moves

class Advisor(Piece):
    def get_valid_moves(self, board):
        moves = []
        r, c = self.position
        potential_moves = [(r+1, c+1), (r+1, c-1), (r-1, c+1), (r-1, c-1)]
        
        for nr, nc in potential_moves:
            if not self._is_in_palace((nr, nc)):
                continue
            
            target_piece = board.get_piece(nr, nc)
            if not self.is_friendly(target_piece):
                moves.append((nr, nc))
                
        return moves

class Elephant(Piece):
    def get_valid_moves(self, board):
        moves = []
        r, c = self.position
        potential_moves = [
            ((-1, -1), (-2, -2)),
            ((-1, 1), (-2, 2)),
            ((1, -1), (2, -2)),
            ((1, 1), (2, 2))
        ]
        
        for (dr_eye, dc_eye), (dr_target, dc_target) in potential_moves:
            eye_r, eye_c = r + dr_eye, c + dc_eye
            target_r, target_c = r + dr_target, c + dc_target

            if not (0 <= target_r < ROWS and 0 <= target_c < COLS):
                continue

            if (self.color == 'black' and target_r > 4) or \
               (self.color == 'red' and target_r < 5):
                continue

            if board.get_piece(eye_r, eye_c) is not EMPTY:
                continue

            target_piece = board.get_piece(target_r, target_c)
            if not self.is_friendly(target_piece):
                moves.append((target_r, target_c))
                
        return moves

class Cannon(Piece):
    def get_valid_moves(self, board):
        moves = []
        r, c = self.position
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            screen_found = False
            
            while 0 <= nr < ROWS and 0 <= nc < COLS:
                target_piece = board.get_piece(nr, nc)
                
                if not screen_found:
                    if target_piece is EMPTY:
                        moves.append((nr, nc))
                    else:
                        screen_found = True
                else: 
                    if target_piece is not EMPTY:
                        if self.is_enemy(target_piece):
                            moves.append((nr, nc))
                        break
                
                nr, nc = nr + dr, nc + dc
        return moves

class Pawn(Piece):
    def get_valid_moves(self, board):
        moves = []
        r, c = self.position

        if self.color == 'red':
            forward_r = r - 1
            river_crossed = (r <= 4)
        else: # 'black'
            forward_r = r + 1
            river_crossed = (r >= 5)

        if 0 <= forward_r < ROWS:
            target_piece = board.get_piece(forward_r, c)
            if not self.is_friendly(target_piece):
                moves.append((forward_r, c))

        if river_crossed:
            for dc in [-1, 1]:
                nc = c + dc
                if 0 <= nc < COLS:
                    target_piece = board.get_piece(r, nc)
                    if not self.is_friendly(target_piece):
                        moves.append((r, nc))
                        
        return moves
        
# --- Ví dụ chạy thử (Test Offline) ---
if __name__ == "__main__":
    my_board = Board()
    red_pawn = my_board.get_piece(6, 4)
    if red_pawn:
        print(f"Các nước đi của {red_pawn}:")
        print(red_pawn.get_valid_moves(my_board))
        
    black_cannon = my_board.get_piece(2, 1)
    if black_cannon:
        print(f"\nCác nước đi của {black_cannon}:")
        print(black_cannon.get_valid_moves(my_board))
        
    print("\n--- Di chuyển Tốt Đen (3,4) -> (4,4) ---")
    my_board.move_piece((3, 4), (4, 4))
    
    if black_cannon:
        print(f"\nCác nước đi MỚI của {black_cannon}:")
        print(black_cannon.get_valid_moves(my_board))
        
    moved_pawn = my_board.get_piece(4, 4)
    if moved_pawn:
        print(f"\nCác nước đi của {moved_pawn} (chưa qua sông):")
        print(moved_pawn.get_valid_moves(my_board))
        
    print("\n--- Di chuyển Tốt Đen (4,4) -> (5,4) ---")
    my_board.move_piece((4, 4), (5, 4))
    moved_pawn_across = my_board.get_piece(5, 4)
    if moved_pawn_across:
        print(f"\nCác nước đi của {moved_pawn_across} (ĐÃ qua sông):")
        print(moved_pawn_across.get_valid_moves(my_board))