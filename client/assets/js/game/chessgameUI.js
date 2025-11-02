const GAME_WIDTH = 400;
const GAME_HEIGHT = 600;
const IMAGES_DIR = 'assets/img';

class ChessGameUI {
  constructor() {
    const canvas = document.createElement('canvas');
    canvas.width = GAME_WIDTH;
    canvas.height = GAME_HEIGHT;

    this.ctx = canvas.getContext('2d');

    // Khởi tạo game logic (class / function từ ChessGame.js)
    this.game = ChessGame(); 

    document.body.appendChild(canvas);
    this.start();
    this.update();
  }

  start() {
    this.game.start();
    this.render();
  }

  render() {
    this.ctx.clearRect(0, 0, GAME_WIDTH, GAME_HEIGHT);
    // TODO: sẽ vẽ bàn cờ + quân ở đây
  }

  update(){
    this.draw();

  }

  draw(){
    let img = new IMG;
    img.src = IMAGES_DIR + '/client/assets/img/ban co.jpg';
    img.onload = ()=> {
        this.ctx.drawIMG(img, 0, 0, GAME_WIDTH, GAME_HEIGHT);
    }

  }

}

new ChessGameUI();
