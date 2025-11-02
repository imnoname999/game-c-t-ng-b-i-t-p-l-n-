// file: frontend/app.js (ĐÃ NÂNG CẤP LOGIC CHIẾU BÍ)

const ws = new WebSocket("ws://localhost:8765");

const statusText = document.getElementById("status-text");
const boardContainer = document.getElementById("board-container");
const boardGrid = document.getElementById("board-grid");
const piecesLayer = document.getElementById("pieces-layer");

let myColor = null;
let currentTurn = null;
let selectedPiecePos = null;
let currentBoardState = [];
let validMoveDots = [];

const pieceUnicodeMap = {
    'General': 'Tướng',
    'Advisor': 'Sĩ',
    'Elephant': 'Tượng',
    'Rook': 'Xe',
    'Cannon': 'Pháo',
    'Knight': 'Mã',
    'Pawn': 'Tốt'
};

// 1. === Xử lý Kết nối WebSocket ===
ws.onopen = () => {
    console.log("Đã kết nối tới server WebSocket.");
    statusText.innerText = "Đang chờ người chơi khác...";
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Nhận tin từ server:", data);

    switch (data.type) {
        case "wait":
            statusText.innerText = data.message;
            break;
        case "start":
            myColor = data.color;
            currentBoardState = data.board;
            currentTurn = data.turn;
            updateStatusText();
            renderBoard();
            break;

        // ==================================
        // === NÂNG CẤP: Lắng nghe "game_update" thay vì "move" ===
        // ==================================
        case "game_update":
            // Cập nhật bàn cờ
            currentBoardState = updateBoardState(currentBoardState, data.from, data.to);
            currentTurn = data.turn; // Sẽ là null nếu game kết thúc
            selectedPiecePos = null;
            renderBoard();

            // Cập nhật Status
            if (data.is_checkmate) {
                // Game kết thúc
                currentTurn = null; // Dừng client
                statusText.style.color = "red";
                statusText.style.fontWeight = "bold";
                if (data.winner === myColor) {
                    statusText.innerText = "CHIẾU BÍ! BẠN THẮNG!";
                } else {
                    statusText.innerText = "CHIẾU BÍ! BẠN THUA.";
                }
            } else if (data.is_check) {
                // Báo Chiếu
                updateStatusText(); // Cập nhật lượt
                statusText.innerText += " (Chiếu!)";
            } else {
                // Nước đi bình thường
                updateStatusText();
            }
            break;
            
        case "valid_moves":
            renderValidMoves(data.moves);
            break;

        case "opponent_left":
            statusText.innerText = "Đối thủ đã thoát. Bạn thắng!";
            currentTurn = null; // Dừng game
            break;
        case "error":
            alert("Lỗi từ server: " + data.message);
            selectedPiecePos = null;
            renderBoard();
            break;
    }
};

ws.onclose = () => {
    console.log("Đã ngắt kết nối.");
    statusText.innerText = "Đã ngắt kết nối server!";
};

ws.onerror = (error) => {
    console.error("Lỗi WebSocket:", error);
    statusText.innerText = "Không thể kết nối đến server. (Nhớ chạy `python backend/main.py` nhé)";
};

// 2. === Hàm Vẽ (Render) ===
function renderBoard() {
    piecesLayer.innerHTML = '';
    
    validMoveDots.forEach(dot => dot.remove());
    validMoveDots = [];

    if (boardGrid.children.length === 0) {
        for (let r = 0; r < 10; r++) {
            for (let c = 0; c < 9; c++) {
                const cell = document.createElement('div');
                cell.classList.add('intersection');
                cell.dataset.row = r;
                cell.dataset.col = c;
                
                cell.addEventListener('click', () => onCellClick(r, c));
                
                boardGrid.appendChild(cell);
            }
        }
    }

    for (let r = 0; r < 10; r++) {
        for (let c = 0; c < 9; c++) {
            const pieceString = currentBoardState[r][c];
            if (pieceString) {
                const pieceElement = createPieceElement(pieceString, r, c);
                piecesLayer.appendChild(pieceElement);
            }
        }
    }
}

function createPieceElement(pieceString, row, col) {
    const [colorPrefix, pieceName] = pieceString.split('_');
    const color = (colorPrefix === 'R') ? 'red' : 'black';
    const pieceElement = document.createElement('div');
    pieceElement.classList.add('piece', color);

    pieceElement.innerText = pieceUnicodeMap[pieceName] || '?';
    
    pieceElement.dataset.row = row;
    pieceElement.dataset.col = col;

    const x = (col + 0.5) * 60;
    const y = (row + 0.5) * 60;
    
    pieceElement.style.left = `${x}px`;
    pieceElement.style.top = `${y}px`;

    pieceElement.addEventListener('click', (e) => {
        e.stopPropagation();
        onCellClick(row, col);
    });

    if (selectedPiecePos && selectedPiecePos[0] === row && selectedPiecePos[1] === col) {
        pieceElement.classList.add('selected');
    }
    return pieceElement;
}

function renderValidMoves(moves) {
    const cellSize = 60; // Lấy từ CSS :root

    moves.forEach(move => {
        const [r, c] = move;
        
        const dot = document.createElement('div');
        dot.classList.add('valid-move-dot');

        const x = (c + 0.5) * cellSize;
        const y = (r + 0.5) * cellSize;

        dot.style.left = `${x}px`;
        dot.style.top = `${y}px`;

        dot.addEventListener('click', (e) => {
            e.stopPropagation();
            onCellClick(r, c); // Giả lập như click vào ô đó
        });

        piecesLayer.appendChild(dot);
        validMoveDots.push(dot); // Lưu lại để xóa sau
    });
}

// 3. === Xử lý Logic Click ===
function onCellClick(row, col) {
    // Nếu game đã kết thúc (currentTurn là null) thì không làm gì
    if (currentTurn !== myColor) {
        // console.log("Chưa đến lượt của bạn hoặc game đã kết thúc.");
        return;
    }

    const clickedPieceString = currentBoardState[row][col];
    const isMyPiece = clickedPieceString &&
                      ((clickedPieceString.startsWith('R_') && myColor === 'red') ||
                       (clickedPieceString.startsWith('B_') && myColor === 'black'));

    if (selectedPiecePos) {
        if (selectedPiecePos[0] === row && selectedPiecePos[1] === col) {
            selectedPiecePos = null;
            renderBoard(); // Xóa chấm
            return;
        }
        if (isMyPiece) {
            selectedPiecePos = [row, col];
            renderBoard(); // Vẽ lại để highlight
            // Gửi yêu cầu lấy nước đi MỚI
            const getMovesData = {
                type: "get_moves",
                pos: [row, col]
            };
            ws.send(JSON.stringify(getMovesData));
            return;
        }
        
        const moveData = {
            type: "move",
            from: selectedPiecePos,
            to: [row, col]
        };
        ws.send(JSON.stringify(moveData));
        selectedPiecePos = null;

    } else {
        if (isMyPiece) {
            selectedPiecePos = [row, col];
            renderBoard(); // Vẽ lại để highlight quân cờ

            const getMovesData = {
                type: "get_moves",
                pos: [row, col]
            };
            ws.send(JSON.stringify(getMovesData));
        }
    }
}

// 4. === Hàm Phụ Trợ ===
function updateStatusText() {
    // Đặt lại style cũ
    statusText.style.color = "black";
    statusText.style.fontWeight = "normal";

    if (currentTurn === null) {
        // Game đã kết thúc, không cập nhật nữa
        return;
    }
    
    if (currentTurn === myColor) {
        statusText.innerText = `Đến lượt bạn (${myColor}).`;
    } else {
        statusText.innerText = `Đang chờ đối thủ (${currentTurn}) đi...`;
    }
}

function updateBoardState(board, from, to) {
    const [r_from, c_from] = from;
    const [r_to, c_to] = to;
    
    board[r_to][c_to] = board[r_from][c_from];
    board[r_from][c_from] = null; // EMPTY
    
    return board;
}