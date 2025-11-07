// =============================
// 🎯 Xiangqi Online - Frontend
// Tác giả: Cải tiến bởi GPT-5
// =============================

// --- 1. KHỞI TẠO KẾT NỐI & PHẦN TỬ DOM ---
const ws = new WebSocket("ws://localhost:8765");

const statusText = document.getElementById("status-text");
const boardContainer = document.getElementById("board-container");
const boardGrid = document.getElementById("board-grid");
const piecesLayer = document.getElementById("pieces-layer");
const redTimerDisplay = document.getElementById("red-timer");
const blackTimerDisplay = document.getElementById("black-timer");
const moveList = document.getElementById("move-list");
const resignButton = document.getElementById("resign-button");

// --- 2. TRẠNG THÁI CLIENT ---
let clientTimerInterval = null;
let myColor = null;
let currentTurn = null;
let selectedPiecePos = null;
let currentBoardState = [];
let validMoveDots = [];
let isGameActive = false;

const localGameState = {
  red_time: 300,
  black_time: 300,
  turn: null,
};

// Map tên quân -> ký hiệu tiếng Việt
const pieceMap = {
  General: "Tướng",
  Advisor: "Sĩ",
  Elephant: "Tượng",
  Rook: "Xe",
  Cannon: "Pháo",
  Knight: "Mã",
  Pawn: "Tốt",
};

// =============================
// 🕒 3. ĐỒNG HỒ (TIMER)
// =============================
function formatTime(s) {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

function updateTimerUI() {
  redTimerDisplay.innerText = `Red: ${formatTime(localGameState.red_time)}`;
  blackTimerDisplay.innerText = `Black: ${formatTime(localGameState.black_time)}`;

  redTimerDisplay.classList.toggle("active-turn", localGameState.turn === "red");
  blackTimerDisplay.classList.toggle("active-turn", localGameState.turn === "black");
}

function startClientTimer() {
  if (clientTimerInterval) clearInterval(clientTimerInterval);
  if (!localGameState.turn) return;

  clientTimerInterval = setInterval(() => {
    if (localGameState.turn === "red") {
      localGameState.red_time = Math.max(0, localGameState.red_time - 0.1);
    } else {
      localGameState.black_time = Math.max(0, localGameState.black_time - 0.1);
    }
    updateTimerUI();
  }, 100);
}

function syncTimers(data) {
  Object.assign(localGameState, {
    red_time: data.red_time,
    black_time: data.black_time,
    turn: data.turn,
  });
  currentTurn = data.turn;
  startClientTimer();
  updateTimerUI();
}

// =============================
// 🧩 4. HIỂN THỊ TRẠNG THÁI
// =============================
function updateStatus() {
  statusText.classList.remove("status-blink");

  if (!isGameActive) return;

  const colorStyle = currentTurn === "red" ? "color:#d60000" : "color:#000";
  if (currentTurn === myColor) {
    statusText.innerHTML = `Đến lượt bạn (<strong style="${colorStyle}">${myColor}</strong>).`;
  } else {
    statusText.innerHTML = `Đang chờ đối thủ (<strong style="${colorStyle}">${currentTurn}</strong>)...`;
  }
}

function addMoveToHistory(from, to, color) {
  const li = document.createElement("li");
  li.classList.add(color === "red" ? "red-move" : "black-move");
  li.textContent = `${color.toUpperCase()} đi từ (${from}) → (${to})`;
  moveList.appendChild(li);
  document.getElementById("move-history-container").scrollTop =
    moveList.scrollHeight;
}

// =============================
// ⚔️ 5. GAME OVER + RESET LOGIC
// =============================
function handleGameOver(winner, reason) {
  isGameActive = false;
  localGameState.turn = null;
  currentTurn = null;
  clearInterval(clientTimerInterval);

  redTimerDisplay.classList.remove("active-turn");
  blackTimerDisplay.classList.remove("active-turn");
  resignButton.style.display = "none";

  let msg = "";
  switch (reason) {
    case "checkmate":
      msg = winner === myColor ? "CHIẾU BÍ! BẠN THẮNG!" : "CHIẾU BÍ! BẠN THUA.";
      break;
    case "stalemate":
      msg = winner === myColor ? "ĐỐI THỦ HẾT NƯỚC ĐI! BẠN THẮNG!" : "BẠN BỊ BÍ! BẠN THUA.";
      break;
    case "timeout":
      msg = winner === myColor ? "ĐỐI THỦ HẾT GIỜ! BẠN THẮNG!" : "BẠN HẾT GIỜ! BẠN THUA.";
      break;
    case "resign":
      msg = winner === myColor ? "Đối thủ đã đầu hàng! BẠN THẮNG!" : "Bạn đã đầu hàng. BẠN THUA.";
      break;
    case "opponent_left":
      msg = "Đối thủ đã thoát. Bạn thắng!";
      break;
    case "disconnect":
      msg = "Mất kết nối server.";
      break;
  }

  statusText.innerText = msg;
  statusText.classList.add("status-blink");

  if (reason === "disconnect") return;

  // Hiển thị kết quả 6s -> đếm ngược 6s -> reload
  setTimeout(() => {
    statusText.classList.remove("status-blink");
    let countdown = 6;
    const interval = setInterval(() => {
      countdown--;
      if (countdown > 0) {
        statusText.innerText = `Tìm trận mới sau ${countdown}s...`;
      } else {
        clearInterval(interval);
        statusText.innerText = "Đang tìm trận mới...";
        window.location.reload();
      }
    }, 1000);
  }, 6000);
}

// =============================
// 🧠 6. RENDER BOARD
// =============================
function renderBoard() {
  piecesLayer.innerHTML = "";
  validMoveDots.forEach((d) => d.remove());
  validMoveDots = [];

  const cellSize = parseInt(getComputedStyle(document.documentElement).getPropertyValue("--cell-size"));

  // Tạo grid nếu chưa có
  if (!boardGrid.children.length) {
    for (let r = 0; r < 10; r++) {
      for (let c = 0; c < 9; c++) {
        const cell = document.createElement("div");
        cell.className = "intersection";
        cell.dataset.row = r;
        cell.dataset.col = c;
        cell.addEventListener("click", () => onCellClick(r, c));
        boardGrid.appendChild(cell);
      }
    }
  }

  // Vẽ quân
  for (let r = 0; r < 10; r++) {
    for (let c = 0; c < 9; c++) {
      const val = currentBoardState[r][c];
      if (!val) continue;

      const [prefix, name] = val.split("_");
      const color = prefix === "R" ? "red" : "black";
      const piece = document.createElement("div");
      piece.classList.add("piece", color);
      piece.innerText = pieceMap[name] || "?";
      piece.dataset.row = r;
      piece.dataset.col = c;

      piece.style.left = `${c * cellSize}px`;
      piece.style.top = `${r * cellSize}px`;

      if (selectedPiecePos && selectedPiecePos[0] === r && selectedPiecePos[1] === c)
        piece.classList.add("selected");

      piece.addEventListener("click", (e) => {
        e.stopPropagation();
        onCellClick(r, c);
      });
      piecesLayer.appendChild(piece);
    }
  }
}

function renderValidMoves(moves) {
  const cellSize = parseInt(getComputedStyle(document.documentElement).getPropertyValue("--cell-size"));
  validMoveDots = moves.map(([r, c]) => {
    const dot = document.createElement("div");
    dot.className = "valid-move-dot";
    dot.style.left = `${c * cellSize}px`;
    dot.style.top = `${r * cellSize}px`;
    dot.addEventListener("click", (e) => {
      e.stopPropagation();
      onCellClick(r, c);
    });
    piecesLayer.appendChild(dot);
    return dot;
  });
}

// =============================
// 🧭 7. LOGIC CLICK
// =============================
function onCellClick(r, c) {
  if (!isGameActive || currentTurn !== myColor) return;

  const clickedPiece = currentBoardState[r][c];
  const isMyPiece =
    clickedPiece &&
    ((clickedPiece.startsWith("R_") && myColor === "red") ||
      (clickedPiece.startsWith("B_") && myColor === "black"));

  if (selectedPiecePos) {
    if (selectedPiecePos[0] === r && selectedPiecePos[1] === c) {
      selectedPiecePos = null;
      renderBoard();
      return;
    }

    if (isMyPiece) {
      selectedPiecePos = [r, c];
      renderBoard();
      ws.send(JSON.stringify({ type: "get_moves", pos: [r, c] }));
      return;
    }

    ws.send(JSON.stringify({ type: "move", from: selectedPiecePos, to: [r, c] }));
    selectedPiecePos = null;
  } else if (isMyPiece) {
    selectedPiecePos = [r, c];
    renderBoard();
    ws.send(JSON.stringify({ type: "get_moves", pos: [r, c] }));
  }
}

// =============================
// 💬 8. SỰ KIỆN WEBSOCKET
// =============================
ws.onopen = () => {
  console.log("✅ Đã kết nối WebSocket.");
  statusText.innerText = "Đang chờ người chơi khác...";
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("📨 Server:", data);

  switch (data.type) {
    case "wait":
      statusText.innerText = data.message;
      break;

    case "start":
      myColor = data.color;
      isGameActive = true;
      currentBoardState = data.board;
      syncTimers(data);
      updateStatus();
      renderBoard();
      resignButton.style.display = "block";
      break;

    case "game_update":
      currentBoardState = updateBoard(currentBoardState, data.from, data.to);
      syncTimers(data);
      updateStatus();
      renderBoard();
      addMoveToHistory(data.from, data.to, data.turn === "red" ? "black" : "red");
      if (data.is_check) statusText.innerHTML += " (Chiếu!)";
      break;

    case "timer_update":
      syncTimers(data);
      break;

    case "valid_moves":
      renderValidMoves(data.moves);
      break;

    case "game_over":
      if (data.from && data.to)
        currentBoardState = updateBoard(currentBoardState, data.from, data.to);
      renderBoard();
      handleGameOver(data.winner, data.reason);
      break;

    case "error":
      alert("Lỗi: " + data.message);
      selectedPiecePos = null;
      renderBoard();
      break;
  }
};

ws.onclose = () => {
  console.warn("⚠️ Mất kết nối server.");
  statusText.innerText = "Đã ngắt kết nối server.";
  handleGameOver(null, "disconnect");
};

ws.onerror = (err) => {
  console.error("❌ Lỗi WebSocket:", err);
  statusText.innerText = "Không thể kết nối đến server.";
};

// =============================
// 🛠️ 9. HÀM PHỤ TRỢ
// =============================
function updateBoard(board, from, to) {
  const b = board.map((r) => [...r]);
  b[to[0]][to[1]] = b[from[0]][from[1]];
  b[from[0]][from[1]] = null;
  return b;
}

function onResignClick() {
  if (!isGameActive || !myColor) return;
  if (confirm("Bạn có chắc chắn muốn đầu hàng?")) {
    ws.send(JSON.stringify({ type: "resign" }));
  }
}

resignButton.addEventListener("click", onResignClick);
