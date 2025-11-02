function chessitems(x, y, name, type) {

    let self = {
        x: x,
        y: y,
        name: name,
        type: type
    };

    function init() {
        // Khởi tạo nếu cần
    }

    init();
    return self;
}

function xe(x, y, type = 0) {
    return chessitems(x, y, 'xe', type);
}

function phao(x, y, type = 0) {
    return chessitems(x, y, 'phao', type);
}

function ma(x, y, type = 0) {
    return chessitems(x, y, 'ma', type);
}

function tuongs(x, y, type = 0) {
    return chessitems(x, y, 'tuongs', type);
}

function sy(x, y, type = 0) {
    return chessitems(x, y, 'sy', type);
}

function tuongj(x, y, type = 0) {
    return chessitems(x, y, 'tuongj', type);
}

function tot(x, y, type = 0) {
    return chessitems(x, y, 'tot', type);
}
