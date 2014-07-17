function (doc) {
    var BASKET_TYPE = "com.shutterstem.basket";
    if (!doc[BASKET_TYPE]) return;
    
    var exports = {};
    // !code lib/date.js
    var date = exports;
    
    var createdSeconds = date.newDate(doc.created).getTime() / 1000;
    emit(createdSeconds, {name:doc.name, photoCount:doc.photos.length});
}
