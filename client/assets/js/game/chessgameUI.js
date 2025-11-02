const GAME_WIDTH = 400;
const GAME_HEIGHT = 600;
const IMAGES_DIR = 'assets/img';

class ChessGameUI {
  constructor() {
    const canvas = document.createElement('canvas');
    canvas.width = GAME_WIDTH;
    canvas.height = GAME_HEIGHT;

    document.body.appendChild(canvas);

    this.ctx = canvas.getContext('2d');
    this.game = ChessGame();
    
    this.start();
  }

  start() {
    this.game.start();
    this.render();
  }

  render() {
    this.ctx.clearRect(0, 0, GAME_WIDTH, GAME_HEIGHT);
    this.drawBoard();
  }

  drawBoard() {
    let img = new Image();
    img.src = IMAGES_DIR + '/ban_co.png'; // Đặt file ảnh đúng tên này

    img.onload = () => {
      this.ctx.drawImage(img, 0, 0, GAME_WIDTH, GAME_HEIGHT);
    };

    img.onerror = () => {
      console.log("Không load được hình bàn cờ!");
    };
  }
}

new ChessGameUI();
