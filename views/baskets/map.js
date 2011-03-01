function (doc) {
    var BASKET_TYPE = "com.shutterstem.basket"
    if (!doc[BASKET_TYPE]) return;
    
    emit(doc.modified || doc.created, doc.name);
}
