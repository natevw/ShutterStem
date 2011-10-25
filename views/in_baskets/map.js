function (doc) {
    var BASKET_TYPE = "com.shutterstem.basket";
    if (!doc[BASKET_TYPE]) return;
    
    var exports = {};
    // !code lib/date.js
    var date = exports;
    
    var createdSeconds = date.newDate(doc.created).getTime() / 1000;
    doc.photos.forEach(function (photo, idx) {
        emit([createdSeconds, doc._id, idx], photo);   // include_docs follows ref!
    });
}
