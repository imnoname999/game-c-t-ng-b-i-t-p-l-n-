// file: frontend/app.js
// --- 1. Khởi tạo kết nối và DOM Elements ---
const ws = new WebSocket("ws://localhost:8765");
const statusText = document.getElementById("status-text");
const boardContainer = document.getElementById("board-container");
const boardGrid = document.getElementById("board-grid");
const piecesLayer = document.getElementById("pieces-layer");
const redTimerDisplay = document.getElementById("red-timer");
const blackTimerDisplay = document.getElementById("black-timer");
const moveList = document.getElementById("move-list");
const resignButton = document.getElementById("resign-button");

// --- 2. Biến trạng thái Client ---
let clientTimerInterval = null;
let localGameState = {
    red_time: 300,
    black_time: 300,
    turn: null
};
let myColor = null;
let currentTurn = null;
let selectedPiecePos = null;
let currentBoardState = [];
let validMoveDots = [];
// ===================================
// === THÊM BIẾN CỜ (FLAG) MỚI ===
// ===================================
let isGameOver = false; // Biến này ngăn hàm handleGameOver chạy 2 lần
// ===================================

// Map tên quân cờ (server) sang TÊN FILE (client)
const pieceImageMap = {
    'General': 'tuong', // Tướng
    'Advisor': 'sy',    // Sĩ
    'Elephant': 'tinh', // Tượng (Tịnh)
    'Rook': 'xe',
    'Cannon': 'phao',
    'Knight': 'ma',
    'Pawn': 'tot'
};

// --- 3. Xử lý Đồng hồ (Timer) ---
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Cập nhật UI đồng hồ
function updateTimerUI() {
    redTimerDisplay.innerText = `Red: ${formatTime(localGameState.red_time)}`;
    blackTimerDisplay.innerText = `Black: ${formatTime(localGameState.black_time)}`;
    // Xóa highlight cũ
    redTimerDisplay.classList.remove('active-turn');
    blackTimerDisplay.classList.remove('active-turn');
    // Thêm highlight mới
    if (localGameState.turn === 'red') {
        redTimerDisplay.classList.add('active-turn');
    } else if (localGameState.turn === 'black') {
        blackTimerDisplay.classList.add('active-turn');
    }
}

// Đồng bộ thời gian từ server (khi bắt đầu, hoặc sau 1 nước đi)
function syncTimersFromServer(data) {
    localGameState.red_time = data.red_time;
    localGameState.black_time = data.black_time;
    localGameState.turn = data.turn;
    currentTurn = data.turn; // Đồng bộ cả 2
    startClientTimer(); // Bắt đầu/Reset lại interval
    updateTimerUI(); // Cập nhật UI ngay
}

// Chạy interval ở client để đồng hồ chạy mượt
function startClientTimer() {
    // Xóa interval cũ (nếu có)
    if (clientTimerInterval) {
        clearInterval(clientTimerInterval);
        clientTimerInterval = null;
    }
    // Chỉ chạy nếu game đang diễn ra
    if (localGameState.turn !== null) {
        clientTimerInterval = setInterval(() => {
            if (localGameState.turn === 'red') {
                localGameState.red_time = Math.max(0, localGameState.red_time - 0.1);
            } else if (localGameState.turn === 'black') {
                localGameState.black_time = Math.max(0, localGameState.black_time - 0.1);
            }
            updateTimerUI();
        }, 100); // Cập nhật 10 lần/giây
    }
}

// --- 4. Xử lý Trạng thái Game (Status, History) ---
// Thêm nước đi vào list UI
function addMoveToHistory(fromPos, toPos, color) {
    const li = document.createElement("li");
    const colorClass = (color === 'red') ? 'red-move' : 'black-move';
    li.classList.add(colorClass);
    li.textContent = `${color.charAt(0).toUpperCase() + color.slice(1)} đi từ (${fromPos}) → (${toPos})`;
    moveList.appendChild(li);
    // Tự động cuộn xuống
    const historyContainer = document.getElementById("move-history-container");
    historyContainer.scrollTop = historyContainer.scrollHeight;
}

// ===============================================
// === HÀM handleGameOver (BẢN FIX "BẤT TỬ") ===
// ===============================================
// Xử lý khi game KẾT THÚC
function handleGameOver(winner, reason) {
    // === FIX 1: DÙNG BIẾN CỜ ĐỂ CHẶN CHẠY 2 LẦN ===
    if (isGameOver) {
        console.warn("handleGameOver đã chạy, chặn lần gọi thứ 2.");
        return;
    }
    // === FIX 2 (CỦA NÍ): CHẶN NẾU ĐÃ KẾT THÚC ===
    // (Kết hợp cả 2 cho chắc)
    if (localGameState.turn === null && reason !== "disconnect") {
        console.warn("Đã xử lý 'game_over', bỏ qua tin nhắn thứ hai.");
        return;
    }

    isGameOver = true; // ĐÁNH DẤU LÀ ĐÃ KẾT THÚC
    // ------------------------------------
    // 1. Dừng game, timer, ẩn nút
    currentTurn = null;
    localGameState.turn = null;
    startClientTimer(); // Dừng interval
    redTimerDisplay.classList.remove('active-turn');
    blackTimerDisplay.classList.remove('active-turn');
    resignButton.style.display = "none";
    // 2. Tạo tin nhắn kết quả
    let statusMessage = "";
    if (reason === "checkmate") {
        statusMessage = (winner === myColor) ? "CHIẾU BÍ! BẠN THẮNG!" : "CHIẾU BÍ! BẠN THUA.";
    } else if (reason === "stalemate") {
        statusMessage = (winner === myColor) ? "ĐỐI THỦ HẾT NƯỚC ĐI! BẠN THẮNG!"
            : "BẠN BỊ BÍ! BẠN THUA.";
    } else if (reason === "timeout") {
        statusMessage = (winner === myColor) ? "ĐỐI THỦ HẾT GIỜ! BẠN THẮNG!" : "BẠN HẾT GIỜ! BẠN THUA.";
    } else if (reason === "opponent_left") {
        statusMessage = "Đối thủ đã thoát. Bạn thắng!";
    } else if (reason === "resign") {
        statusMessage = (winner === myColor) ? "Đối thủ đã đầu hàng! BẠN THẮNG!"
            : "Bạn đã đầu hàng. BẠN THUA.";
    } else if (reason === "disconnect") {
        statusMessage = "Mất kết nối server.";
    }
    // 3. Hiển thị tin nhắn kết quả
    statusText.innerText = statusMessage;
    // BẬT nhấp nháy
    statusText.classList.add('status-blink');
    // 4. Nếu rớt mạng thì không tìm trận mới
    if (reason === "disconnect") {
        return;
    }
    // 5. LÊN LỊCH ĐẾM NGƯỢC 12 GIÂY (THEO Ý NÍ)
    const initialWait = 6000;  // 6 giây xem kết quả
    const countdownSeconds = 6;  // 6 giây đếm ngược
    let countdown = countdownSeconds;
    // 5.1. Chờ 10 giây...
    setTimeout(() => {
        // 5.2. ...TẮT nhấp nháy
        statusText.classList.remove('status-blink');
        // 5.3. Bắt đầu đếm ngược 10 giây
        statusText.innerText = `Tìm trận mới sau ${countdown}s...`;
        const countdownInterval = setInterval(() => {
            countdown--;
            if (countdown > 0) {
                statusText.innerText = `Tìm trận mới sau ${countdown}s...`;
            } else {
                // Hết 10 giây đếm ngược
                clearInterval(countdownInterval);
                statusText.innerText = "Đang tìm trận mới...";
                window.location.reload(); // Tải lại trang
            }
        }, 1000);
    }, initialWait);
}
// ===============================================
// ===============================================

// Cập nhật thanh trạng thái (cho mỗi lượt đi)
function updateStatusText() {
    // Xóa blink nếu có
    statusText.classList.remove('status-blink');
    if (currentTurn === null) {
        // Game đã kết thúc, handleGameOver sẽ lo
        return;
    }
    let turnColor = currentTurn;
    let turnStyle = (turnColor === 'red') ? 'color: #d60000;' : 'color: #000;';
    if (currentTurn === myColor) {
        statusText.innerHTML = `Đến lượt bạn (<strong style="${turnStyle}">${myColor}</strong>).`;
    } else {
        statusText.innerHTML = `Đang chờ đối thủ (<strong style="${turnStyle}">${currentTurn}</strong>) đi...`;
    }
}

// *** Xử lý click nút Đầu hàng ***
function onResignClick() {
    // Chỉ chạy nếu game đang diễn ra (myColor đã được set)
    if (myColor && currentTurn !== null) {
        if (confirm("Bạn có chắc chắn muốn đầu hàng ván cờ này?")) {
            ws.send(JSON.stringify({ type: "resign" }));
        }
    }
}
resignButton.addEventListener('click', onResignClick);

// --- 5. Lắng nghe WebSocket Events ---
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
            isGameOver = false; // Reset cờ khi game mới bắt đầu
            myColor = data.color;
            currentBoardState = data.board;
            syncTimersFromServer(data); // Bắt đầu game, đồng bộ timer
            updateStatusText(); // Cập nhật status
            renderBoard(); // Vẽ bàn cờ
            resignButton.style.display = "block";
            break;
        case "game_update":
            // 1. Cập nhật bàn cờ
            currentBoardState = updateBoardState(currentBoardState, data.from, data.to);
            selectedPiecePos = null;
            renderBoard(); // Vẽ lại bàn cờ (xóa chấm, highlight)
            // 2. Đồng bộ timer và lượt
            syncTimersFromServer(data);
            // 3. Cập nhật status
            updateStatusText();
            if (data.is_check) {
                statusText.innerHTML += " (Chiếu!)";
            }
            // 4. Thêm lịch sử
            const movedColor = (data.turn === 'red') ? 'black' : 'red';
            addMoveToHistory(data.from, data.to, movedColor);
            break;
        case "timer_update":
            // Chỉ đồng bộ timer (server gửi mỗi giây)
            localGameState.red_time = data.red_time;
            localGameState.black_time = data.black_time;
            localGameState.turn = data.turn;
            currentTurn = data.turn;
            updateTimerUI(); // Cập nhật UI
            break;
        case "game_over":
            // Cập nhật bàn cờ lần cuối (nếu là chiếu bí/bí)
            if (data.from && data.to) {
                currentBoardState = updateBoardState(currentBoardState, data.from, data.to);
                renderBoard();
                // Thêm nước đi cuối vào lịch sử
                const lastMoveColor = (data.winner === 'red') ? 'red' : 'black';
                addMoveToHistory(data.from, data.to, lastMoveColor);
            }
            // Gọi hàm xử lý chung
            handleGameOver(data.winner, data.reason);
            break;
        case "valid_moves":
            // Server trả về các nước đi hợp lệ
            renderValidMoves(data.moves);
            break;
        case "error":
            alert("Lỗi từ server: " + data.message);
            selectedPiecePos = null; // Bỏ chọn
            renderBoard(); // Vẽ lại (để xóa chấm, highlight)
            break;
    }
};

ws.onclose = () => {
    console.log("Đã ngắt kết nối.");
    statusText.innerText = "Đã ngắt kết nối server!";
    handleGameOver(null, "disconnect"); // Dừng timer nếu rớt mạng
};

ws.onerror = (error) => {
    console.error("Lỗi WebSocket:", error);
    statusText.innerText = "Không thể kết nối đến server.";
};

// --- 6. Hàm Vẽ (Render) ---
function renderBoard() {
    // Xóa quân cờ cũ và chấm cũ
    piecesLayer.innerHTML = '';
    validMoveDots.forEach(dot => dot.remove());
    validMoveDots = [];
    const cellSize = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--cell-size'));

    // Chỉ vẽ lưới 1 lần (khi boardGrid rỗng)
    if (boardGrid.children.length === 0) {
        for (let r = 0; r < 10; r++) {
            for (let c = 0; c < 9; c++) {
                const cell = document.createElement('div');
                cell.classList.add('intersection');
                cell.dataset.row = r;
                cell.dataset.col = c;
                // Bắt sự kiện click vào GIAO ĐIỂM (ô trống)
                cell.addEventListener('click', () => onCellClick(r, c));
                boardGrid.appendChild(cell);
            }
        }
    }

    // Vẽ quân cờ
    for (let r = 0; r < 10; r++) {
        for (let c = 0; c < 9; c++) {
            const pieceString = currentBoardState[r][c];
            if (pieceString) {
                const pieceElement = createPieceElement(pieceString, r, c, cellSize);
                piecesLayer.appendChild(pieceElement);
            }
        }
    }
}

// === Hàm tạo quân cờ (Đã sửa dùng ảnh) ===
function createPieceElement(pieceString, row, col, cellSize) {
    const [colorPrefix, pieceName] = pieceString.split('_'); // Vd: "R", "Rook"

    // Lấy tên file từ map
    const imageName = pieceImageMap[pieceName]; // Vd: "xe"
    // Lấy hậu tố màu
    const colorSuffix = (colorPrefix === 'R') ? 'r' : 'b'; // Vd: "r"

    // Ghép lại thành class CSS, Vd: "xe_r"
    const pieceClassName = `${imageName}_${colorSuffix}`;
    const pieceElement = document.createElement('div');
    pieceElement.classList.add('piece'); // Class chung
    if (imageName) {
        pieceElement.classList.add(pieceClassName); // Class riêng cho quân cờ
    } else {
        pieceElement.innerText = '?'; // Dự phòng nếu server gửi tên lạ
    }

    pieceElement.dataset.row = row;
    pieceElement.dataset.col = col;

    // Đặt quân cờ vào đúng vị trí giao điểm
    // ========================================================
    // === 🎯 CHỖ SỬA 1: DỊCH CHUYỂN QUÂN CỜ VÀO GIỮA Ô ===
    // ========================================================
    // Tọa độ X = (cột * kích thước) + một nửa kích thước
    const x = (col * cellSize) + (cellSize / 2);
    // Tọa độ Y = (hàng * kích thước) + một nửa kích thước
    const y = (row * cellSize) + (cellSize / 2);
    // ========================================================

    pieceElement.style.left = `${x}px`;
    pieceElement.style.top = `${y}px`;

    // Bắt sự kiện click vào QUÂN CỜ
    pieceElement.addEventListener('click', (e) => {
        e.stopPropagation(); // Ngăn click vào ô (intersection) bên dưới
        onCellClick(row, col);
    });

    // Highlight nếu đang được chọn
    if (selectedPiecePos && selectedPiecePos[0] === row && selectedPiecePos[1] === col) {
        pieceElement.classList.add('selected');
    }
    return pieceElement;
}

// ========================================================
// Vẽ các chấm gợi ý nước đi
function renderValidMoves(moves) {
    const cellSize = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--cell-size'));
    moves.forEach(move => {
        const [r, c] = move;
        const dot = document.createElement('div');
        dot.classList.add('valid-move-dot');

        // ========================================================
        // === 🎯 CHỖ SỬA 2: DỊCH CHUYỂN CHẤM VÀO GIỮA Ô ===
        // ========================================================
        const x = (c * cellSize) + (cellSize / 2);
        const y = (r * cellSize) + (cellSize / 2);
        // ========================================================

        dot.style.left = `${x}px`;
        dot.style.top = `${y}px`;

        // Bắt sự kiện click vào CHẤM
        dot.addEventListener('click', (e) => {
            e.stopPropagation(); // Ngăn click vào ô bên dưới
            onCellClick(r, c); // Coi như click vào ô đó
        });
        piecesLayer.appendChild(dot);
        validMoveDots.push(dot); // Lưu lại để xóa
    });
}

// --- 7. Xử lý Logic Click (Quan trọng) ---
function onCellClick(row, col) {
    // Nếu không phải lượt mình (hoặc game đã hết) thì không làm gì
    if (currentTurn !== myColor) {
        return;
    }

    const clickedPieceString = currentBoardState[row][col];
    // Kiểm tra xem ô vừa click có phải là quân của mình không
    const isMyPiece = clickedPieceString &&
        ((clickedPieceString.startsWith('R_') && myColor === 'red') ||
            (clickedPieceString.startsWith('B_') && myColor === 'black'));

    if (selectedPiecePos) {
        // --- 1. ĐÃ CHỌN QUÂN, CLICK LẦN 2 ---

        // Click lại chính nó -> Bỏ chọn
        if (selectedPiecePos[0] === row && selectedPiecePos[1] === col) {
            selectedPiecePos = null;
            renderBoard(); // Xóa chấm, xóa highlight
            return;
        }

        // Click vào 1 quân khác của mình -> Đổi quân chọn
        if (isMyPiece) {
            selectedPiecePos = [row, col];
            renderBoard(); // Vẽ lại (xóa chấm cũ, highlight quân mới)
            ws.send(JSON.stringify({ type: "get_moves", pos: [row, col] }));
            return;
        }

        // Click vào ô trống hoặc quân địch -> Thực hiện nước đi
        const moveData = {
            type: "move",
            from: selectedPiecePos,
            to: [row, col]
        };
        ws.send(JSON.stringify(moveData));
        selectedPiecePos = null; // Xóa chọn sau khi gửi
        // Không renderBoard() ở đây, client PHẢI đợi "game_update" từ server

    } else {
        // --- 2. CHƯA CHỌN QUÂN, CLICK LẦN 1 ---
        if (isMyPiece) {
            // Click vào quân của mình -> Chọn nó
            selectedPiecePos = [row, col];
            renderBoard(); // Vẽ highlight
            ws.send(JSON.stringify({ type: "get_moves", pos: [row, col] }));
        }
    }
}

// --- 8. Hàm Phụ Trợ (Utils) ---
// Cập nhật state bàn cờ (local)
function updateBoardState(board, from, to) {
    const [r_from, c_from] = from;
    const [r_to, c_to] = to;
    // Phải deep copy mảng 2 chiều
    const newBoard = board.map(row => [...row]);
    newBoard[r_to][c_to] = newBoard[r_from][c_from];
    newBoard[r_from][c_from] = null; // EMPTY
    return newBoard;
}