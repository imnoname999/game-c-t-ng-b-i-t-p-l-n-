const ROWS = 9;
const COLS = 9;

function chessgame() {
  const GAME = [
    xe(0,0),ma(1,0), tuongj(2,0), sy(3,0), tuongs(4,0), sy(5,0), tuongj(6,0), ma(7,0), xe(8,0),
    phao(1,2), phao(7,2),
    tot(0,3),tot(2,3),tot(4,3),tot(6,3),tot(8,3),
    tot(0,3,1),tot(2,3,1),tot(4,3,1),tot(6,3,1),tot(8,3,1),
    phao(1,2,1), phao(7,2,1),
     xe(0,0,1),ma(1,0,1), tuongj(2,0,1), sy(3,0,1), tuongs(4,0,1), sy(5,0,1), tuongj(6,0,1), ma(7,0,1), xe(8,0,1)

  ];
let items;

    let self ={};
    function restart() {
      items = Object.assign(GAME);
      
    }

    self.start = function () { 
      restart();
    }
  self.pause = function () {

    }
  self.end = function () { 

    }

    function  init () {
      restart();
      Object.defineProperties(self, {
        items: {get:function(){return items }}
      });
        
    }init( );
    return self;
}
console.dir(new chessgame);