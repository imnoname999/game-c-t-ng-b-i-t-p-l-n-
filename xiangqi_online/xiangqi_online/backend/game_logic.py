# file: backend/game_logic.py
# Hằng số
ROWS = 10
COLS = 9
EMPTY = None

# --- CLASS CHA (Piece) ---
class Piece:
    """Class cha cho tất cả các quân cờ."""
    
    def __init__(self, color, position):
        self.color = color
        self.position = position
        self.name = self.__class__.__name__

    def __repr__(self):
        """Hàm này để debug ở server, cho ra output đẹp."""
        names_unicode = {
            'General': 'Tướng', 'Advisor': 'Sĩ', 'Elephant': 'Tượng',
            'Rook': 'Xe', 'Cannon': 'Pháo', 'Knight': 'Mã', 'Pawn': 'Tốt'
        }
        color_prefix = 'B' if self.color == 'black' else 'R'
        return f"{color_prefix}{names_unicode.get(self.name, self.name)}@({self.position[0]},{self.position[1]})"

    def is_valid_move(self, board, new_pos):
        """Kiểm tra xem new_pos có trong danh sách nước đi CƠ BẢN không."""
        return new_pos in self.get_valid_moves(board)

    def get_valid_moves(self, board):
        """
        Lấy các nước đi CƠ BẢN (chưa lọc tự chiếu).
        Hàm này BẮT BUỘC phải được override (ghi đè) ở các class con.
        """
        raise NotImplementedError("Phải override trong class con")

    def get_legal_moves(self, board):
        """
        Lấy các nước đi HỢP LỆ (đã lọc các nước 'tự chiếu').
        Hàm này là cốt lõi, nó dùng chung cho TẤT CẢ các quân cờ.
        """
        legal_moves = []
        # 1. Lấy các nước đi cơ bản (chưa lọc)
        pseudo_legal_moves = self.get_valid_moves(board)
        
        for move in pseudo_legal_moves:
            # 2. Dùng 'test_move' để đi thử
            # (context manager 'for' sẽ tự động hoàn lại bàn cờ)
            for _ in board.test_move(self.position, move):
                # 3. Sau khi đi thử, kiểm tra xem Tướng của mình có bị chiếu không
                if not board.is_in_check(self.color):
                    # 4. Nếu không bị chiếu -> đây là nước đi hợp lệ
                    legal_moves.append(move)
                    
        return legal_moves

    def is_enemy(self, piece):
        """Kiểm tra piece có phải quân địch không."""
        return piece is not EMPTY and piece.color != self.color

    def is_friendly(self, piece):
        """Kiểm tra piece có phải quân mình không."""
        return piece is not EMPTY and piece.color == self.color
        
    def _is_in_palace(self, pos):
        """Kiểm tra 1 vị trí có nằm trong Cung Tướng không."""
        r, c = pos
        if not (3 <= c <= 5):
            return False
        if self.color == 'red':
            return 7 <= r <= 9
        else: # 'black'
            return 0 <= r <= 2

# --- CLASS BÀN CỜ (Board) ---
class Board:
    """Class đại diện cho bàn cờ."""
    
    def __init__(self):
        # self.grid là một list 2 chiều 10x9
        self.grid = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        self.setup_pieces()
        # Lưu vị trí Tướng để tối ưu hóa kiểm tra chiếu
        self.red_general_pos = (9, 4)
        self.black_general_pos = (0, 4)
        self.ROWS = ROWS
        self.COLS = COLS

    def setup_pieces(self):
        """Khởi tạo bàn cờ với vị trí ban đầu."""
        
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
        """Lấy quân cờ tại (row, col) một cách an toàn."""
        if 0 <= row < ROWS and 0 <= col < COLS:
            return self.grid[row][col]
        return None

    def move_piece(self, from_pos, to_pos):
        """Di chuyển quân cờ (thật)."""
        r_from, c_from = from_pos
        r_to, c_to = to_pos
        
        piece = self.get_piece(r_from, c_from)
        if piece:
            captured_piece = self.get_piece(r_to, c_to)
            
            # Cập nhật vị trí Tướng nếu Tướng di chuyển
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
        """Kiểm tra luật "Lộ mặt Tướng"."""
        r_red, c_red = self.red_general_pos
        r_black, c_black = self.black_general_pos
        
        # Nếu không cùng cột, chắc chắn không lộ mặt
        if c_red != c_black:
            return False
            
        # Kiểm tra các ô ở giữa
        for r in range(r_black + 1, r_red):
            if self.get_piece(r, c_red) is not EMPTY:
                return False # Có quân cản, không lộ mặt
                
        return True # Không có quân cản, lộ mặt!

    def is_in_check(self, color):
        """Kiểm tra xem Tướng của phe 'color' có đang bị chiếu không."""
        if color == 'red':
            my_general_pos = self.red_general_pos
            enemy_color = 'black'
        else:
            my_general_pos = self.black_general_pos
            enemy_color = 'red'
            
        # Lấy tất cả quân của địch
        enemy_pieces = []
        for r in range(self.ROWS):
            for c in range(self.COLS):
                piece = self.get_piece(r, c)
                if piece and piece.color == enemy_color:
                    enemy_pieces.append(piece)
        
        # Kiểm tra xem có quân địch nào có thể ăn Tướng không
        # (Dùng get_valid_moves thay vì get_legal_moves để tránh đệ quy vô hạn)
        for piece in enemy_pieces:
            moves = piece.get_valid_moves(self)
            if my_general_pos in moves:
                return True # Bị chiếu!
                
        # Kiểm tra trường hợp đặc biệt: Lộ mặt Tướng
        if self.is_generals_facing():
             return True # Bị chiếu!
             
        return False # An toàn

    def test_move(self, from_pos, to_pos):
        """
        'Mô phỏng' một nước đi. Dùng làm context manager (với 'yield').
        Nó sẽ di chuyển, 'yield', rồi hoàn lại nước đi.
        """
        r_from, c_from = from_pos
        r_to, c_to = to_pos
        piece_to_move = self.get_piece(r_from, c_from)
        
        if not piece_to_move:
            yield
            return
            
        # --- Lưu lại trạng thái cũ ---
        captured_piece = self.get_piece(r_to, c_to)
        original_pos = piece_to_move.position
        # Lưu vị trí Tướng cũ (rất quan trọng)
        old_red_gen_pos = self.red_general_pos
        old_black_gen_pos = self.black_general_pos

        # --- Thực hiện nước đi thử ---
        self.grid[r_to][c_to] = piece_to_move
        self.grid[r_from][c_from] = EMPTY
        piece_to_move.position = to_pos
        
        # Cập nhật vị trí Tướng (thử)
        if isinstance(piece_to_move, General):
            if piece_to_move.color == 'red':
                self.red_general_pos = to_pos
            else:
                self.black_general_pos = to_pos
        
        try:
            yield # <- Tại đây, code trong get_legal_moves sẽ chạy
        finally:
            # --- Hoàn lại trạng thái cũ ---
            self.grid[r_from][c_from] = piece_to_move
            self.grid[r_to][c_to] = captured_piece
            piece_to_move.position = original_pos
            # Hoàn lại vị trí Tướng
            self.red_general_pos = old_red_gen_pos
            self.black_general_pos = old_black_gen_pos

    def is_checkmate(self, color):
        """Kiểm tra xem phe 'color' có bị Chiếu Bí không."""
        # 1. Phải đang bị chiếu
        if not self.is_in_check(color):
            return False
            
        # 2. Lấy tất cả quân của mình
        my_pieces = []
        for r in range(self.ROWS):
            for c in range(self.COLS):
                piece = self.get_piece(r, c)
                if piece and piece.color == color:
                    my_pieces.append(piece)
        
        # 3. Kiểm tra xem có BẤT KỲ quân nào có nước đi HỢP LỆ không
        for piece in my_pieces:
            # Dùng get_legal_moves (đã lọc tự chiếu)
            if len(piece.get_legal_moves(self)) > 0:
                return False # Vẫn còn nước đi, chưa bị chiếu bí
                
        return True # Đang bị chiếu VÀ hết nước đi -> Chiếu Bí!

    def is_stalemate(self, color):
        """Kiểm tra xem phe 'color' có bị 'Bí' (Stalemate) không."""
        # 1. KHÔNG được đang bị chiếu
        if self.is_in_check(color):
            return False
        
        # 2. Lấy tất cả các quân
        my_pieces = []
        for r in range(self.ROWS):
            for c in range(self.COLS):
                piece = self.get_piece(r, c)
                if piece and piece.color == color:
                    my_pieces.append(piece)
        
        # 3. Kiểm tra xem có BẤT KỲ nước đi hợp lệ nào không
        for piece in my_pieces:
            if len(piece.get_legal_moves(self)) > 0:
                return False # Vẫn còn nước đi, không "Bí"
                
        # Không bị chiếu VÀ không còn nước đi -> "Bí" (thua)
        return True

# --- LOGIC CÁC QUÂN CỜ (FULL) ---

class Rook(Piece):
    """Quân Xe"""
    def get_valid_moves(self, board):
        moves = []
        r, c = self.position
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)] # Ngang, Dọc
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while 0 <= nr < ROWS and 0 <= nc < COLS:
                target_piece = board.get_piece(nr, nc)
                if target_piece is EMPTY:
                    moves.append((nr, nc))
                elif self.is_enemy(target_piece):
                    moves.append((nr, nc)) # Ăn quân
                    break # Dừng lại
                else: # là quân mình
                    break # Dừng lại
                nr, nc = nr + dr, nc + dc
        return moves

class Knight(Piece):
    """Quân Mã"""
    def get_valid_moves(self, board):
        moves = []
        r, c = self.position
        # (dr_leg, dc_leg) là ô cản chân
        # (dr_target, dc_target) là ô đích
        potential_moves = [
            ((-1, 0), (-2, 1)), ((-1, 0), (-2, -1)), # Lên
            ((1, 0), (2, 1)), ((1, 0), (2, -1)),   # Xuống
            ((0, -1), (-1, -2)), ((0, -1), (1, -2)), # Trái
            ((0, 1), (-1, 2)), ((0, 1), (1, 2))    # Phải
        ]
        
        for (dr_leg, dc_leg), (dr_target, dc_target) in potential_moves:
            leg_r, leg_c = r + dr_leg, c + dc_leg
            target_r, target_c = r + dr_target, c + dc_target
            
            # Kiểm tra ô đích có trong bàn cờ không
            if not (0 <= target_r < ROWS and 0 <= target_c < COLS):
                continue
            
            # Kiểm tra ô cản chân
            leg_piece = board.get_piece(leg_r, leg_c)
            if leg_piece is not EMPTY:
                continue # Bị cản
            
            # Kiểm tra ô đích
            target_piece = board.get_piece(target_r, target_c)
            if target_piece is EMPTY or self.is_enemy(target_piece):
                moves.append((target_r, target_c))
                
        return moves

class General(Piece):
    """Quân Tướng (Soái)"""
    def get_valid_moves(self, board):
        moves = []
        r, c = self.position
        potential_moves = [(r+1, c), (r-1, c), (r, c+1), (r, c-1)]
        
        # Lấy vị trí Tướng địch để kiểm tra luật "lộ mặt"
        enemy_gen_pos = board.black_general_pos if self.color == 'red' else board.red_general_pos
        
        for nr, nc in potential_moves:
            # 1. Phải ở trong Cung
            if not self._is_in_palace((nr, nc)):
                continue
                
            # 2. Ô đích không phải quân mình
            target_piece = board.get_piece(nr, nc)
            if self.is_friendly(target_piece):
                continue
                
            # 3. Kiểm tra "Lộ mặt" (nếu di chuyển đến cùng cột với Tướng địch)
            if nc != enemy_gen_pos[1]:
                moves.append((nr, nc)) # Khác cột, an toàn
            else:
                # Cùng cột, kiểm tra xem có bị lộ mặt không
                is_safe = False
                min_r, max_r = sorted((nr, enemy_gen_pos[0]))
                for check_r in range(min_r + 1, max_r):
                    if board.get_piece(check_r, nc) is not EMPTY:
                        is_safe = True # Có quân cản
                        break
                if is_safe:
                    moves.append((nr, nc))
                    
        return moves

class Advisor(Piece):
    """Quân Sĩ"""
    def get_valid_moves(self, board):
        moves = []
        r, c = self.position
        potential_moves = [(r+1, c+1), (r+1, c-1), (r-1, c+1), (r-1, c-1)] # 4 ô chéo
        
        for nr, nc in potential_moves:
            # 1. Phải ở trong Cung
            if not self._is_in_palace((nr, nc)):
                continue
            
            # 2. Ô đích không phải quân mình
            target_piece = board.get_piece(nr, nc)
            if not self.is_friendly(target_piece):
                moves.append((nr, nc))
                
        return moves

class Elephant(Piece):
    """Quân Tượng (Tịnh)"""
    def get_valid_moves(self, board):
        moves = []
        r, c = self.position
        # (dr_eye, dc_eye) là ô cản (chân Tượng)
        # (dr_target, dc_target) là ô đích
        potential_moves = [
            ((-1, -1), (-2, -2)), # Lên trái
            ((-1, 1), (-2, 2)),   # Lên phải
            ((1, -1), (2, -2)),   # Xuống trái
            ((1, 1), (2, 2))      # Xuống phải
        ]
        
        for (dr_eye, dc_eye), (dr_target, dc_target) in potential_moves:
            eye_r, eye_c = r + dr_eye, c + dc_eye
            target_r, target_c = r + dr_target, c + dc_target
            
            # 1. Ô đích phải trong bàn cờ
            if not (0 <= target_r < ROWS and 0 <= target_c < COLS):
                continue
                
            # 2. Không được qua sông
            if (self.color == 'black' and target_r > 4) or \
               (self.color == 'red' and target_r < 5):
                continue
                
            # 3. Không bị cản chân Tượng
            if board.get_piece(eye_r, eye_c) is not EMPTY:
                continue
                
            # 4. Ô đích không phải quân mình
            target_piece = board.get_piece(target_r, target_c)
            if not self.is_friendly(target_piece):
                moves.append((target_r, target_c))
                
        return moves

class Cannon(Piece):
    """Quân Pháo"""
    def get_valid_moves(self, board):
        moves = []
        r, c = self.position
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)] # Ngang, Dọc
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            screen_found = False # Biến đếm "ngòi"
            
            while 0 <= nr < ROWS and 0 <= nc < COLS:
                target_piece = board.get_piece(nr, nc)
                
                if not screen_found:
                    # 1. CHƯA GẶP NGÒI
                    if target_piece is EMPTY:
                        moves.append((nr, nc)) # Di chuyển
                    else:
                        screen_found = True # Gặp ngòi
                else:
                    # 2. ĐÃ GẶP NGÒI
                    if target_piece is not EMPTY:
                        if self.is_enemy(target_piece):
                            moves.append((nr, nc)) # Ăn quân
                        break # Dừng (dù là quân mình hay địch)
                
                nr, nc = nr + dr, nc + dc
        return moves

class Pawn(Piece):
    """Quân Tốt (Binh)"""
    def get_valid_moves(self, board):
        moves = []
        r, c = self.position
        
        if self.color == 'red':
            forward_r = r - 1 # Tiến lên (giảm row)
            river_crossed = (r <= 4)
        else: # 'black'
            forward_r = r + 1 # Tiến lên (tăng row)
            river_crossed = (r >= 5)
            
        # 1. Nước đi thẳng
        if 0 <= forward_r < ROWS:
            target_piece = board.get_piece(forward_r, c)
            if not self.is_friendly(target_piece):
                moves.append((forward_r, c))
                
        # 2. Nước đi ngang (chỉ khi đã qua sông)
        if river_crossed:
            for dc in [-1, 1]: # Trái, Phải
                nc = c + dc
                if 0 <= nc < COLS: # Kiểm tra biên ngang
                    target_piece = board.get_piece(r, nc)
                    if not self.is_friendly(target_piece):
                        moves.append((r, nc))
                        
        return moves
        
# --- Ví dụ chạy thử (Test Offline) ---
if __name__ == "__main__":
    # Ní có thể chạy `python backend/game_logic.py để test logic
    my_board = Board()
    
    red_pawn = my_board.get_piece(6, 4)
    if red_pawn:
        print(f"Các nước đi của {red_pawn} (chưa qua sông):")
        print(red_pawn.get_valid_moves(my_board)) # Output: [(5, 4)]
        
    print("\n--- Di chuyển Tốt Đỏ (6,4) -> (5,4) -> (4,4) ---")
    my_board.move_piece((6, 4), (5, 4))
    my_board.move_piece((5, 4), (4, 4))
    
    moved_pawn_across = my_board.get_piece(4, 4)
    if moved_pawn_across:
        print(f"Các nước đi của {moved_pawn_across} (ĐÃ qua sông):")
        print(moved_pawn_across.get_valid_moves(my_board)) # Output: [(3, 4), (4, 3), (4, 5)]
        
    print("\n--- Test Pháo ---")
    black_cannon = my_board.get_piece(2, 1)
    if black_cannon:
        print(f"Các nước đi của {black_cannon} (chưa bị cản):")
        # Sẽ có (2,0), (2,2), (2,3),... (2,7)
        print(black_cannon.get_valid_moves(my_board)) 
        
    print("\n--- Di chuyển Tốt Đen (3,4) -> (4,4) (BỊ ĂN) ---")
    # Pháo (2,1) sẽ thấy Tốt (3,4) là ngòi, và Tốt (4,4) là quân địch
    my_board.move_piece((3, 4), (4, 4)) # Tốt đen ăn Tốt đỏ
    
    if black_cannon:
        print(f"Các nước đi MỚI của {black_cannon}:")
        # Nước (2,4) sẽ xuất hiện
        print(black_cannon.get_valid_moves(my_board))
