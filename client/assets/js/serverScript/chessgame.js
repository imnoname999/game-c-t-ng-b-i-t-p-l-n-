const ROWS = 10;
const COLS = 9;

function piece(type, x, y, team) {
  return { type, x, y, team };
}

function ChessGame() {
  const GAME = [
    // Đen (team=0)
    piece("xe",0,0,0), piece("ma",1,0,0), piece("tuong",2,0,0), piece("sy",3,0,0),
    piece("tuong_s",4,0,0), piece("sy",5,0,0), piece("tuong",6,0,0),
    piece("ma",7,0,0), piece("xe",8,0,0),

    piece("phao",1,2,0), piece("phao",7,2,0),
    piece("tot",0,3,0), piece("tot",2,3,0), piece("tot",4,3,0), piece("tot",6,3,0), piece("tot",8,3,0),

    // Đỏ (team=1)
    piece("xe",0,9,1), piece("ma",1,9,1), piece("tuong",2,9,1), piece("sy",3,9,1),
    piece("tuong_s",4,9,1), piece("sy",5,9,1), piece("tuong",6,9,1),
    piece("ma",7,9,1), piece("xe",8,9,1),

    piece("phao",1,7,1), piece("phao",7,7,1),
    piece("tot",0,6,1), piece("tot",2,6,1), piece("tot",4,6,1), piece("tot",6,6,1), piece("tot",8,6,1)
  ];

  let items = [...GAME];

  return {
    start: () => items = [...GAME],
    items
  };
}
