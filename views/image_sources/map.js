function (doc) {
    var IMAGE_SOURCE_TYPE = "com.shutterstem.image-source"
    if (!doc[IMAGE_SOURCE_TYPE]) return;
    
    emit(doc.modified || doc.created, doc.name);
}
