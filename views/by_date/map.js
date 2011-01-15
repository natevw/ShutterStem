function (doc) {
    var IMAGE_TYPE = "testtype-image";
    if (!doc[IMAGE_TYPE]) return;
    
    var exports = {};
    // !code lib/date.js
    var date = exports;
    
    emit(date.toUTCComponents(date.newDate(doc.timestamp)));
}
