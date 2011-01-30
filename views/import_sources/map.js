function (doc) {
    var IMPORT_SOURCE_TYPE = "testtype-import_source";
    if (!doc[IMPORT_SOURCE_TYPE]) return;
    
    emit(doc.modified || doc.created, doc.name);
}
