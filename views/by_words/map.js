function (doc) {
    var IMAGE_TYPE = "com.shutterstem.image";
    if (!doc[IMAGE_TYPE]) return;
    if (!doc.description) return;
    
    var words = doc.description.split(/\s+/).map(function (w) { return w.replace(/\W/g, '').toLowerCase(); });
    words.forEach(function (w) {
        if (w) emit(w);
    });
}
