exports.rows = function (callback) {
    callback || (callback = function (r) { return r; });
    
    var firstRow, currentRow, lastRow;
    firstRow = currentRow = getRow();
    function rower() {
        var value;
        if (currentRow) {
            lastRow = currentRow;
            value = callback(currentRow);
            currentRow = getRow();
        }
        return value;
    }
    rower.first = function (cb) {
        cb || (cb = callback);
        return function () {
            return cb(firstRow);
        };
    }
    rower.last = function (cb) {
        cb || (cb = callback);
        return function () {
            if (currentRow) {
                throw Error("Last row must not be accessed until iteration is complete!");
            }
            return cb(lastRow);
        };
    }
    rower.iterator = true;
    return rower;
}
