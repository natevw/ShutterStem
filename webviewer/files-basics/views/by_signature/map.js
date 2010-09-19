function(doc) {
  if (doc.sha1) {
    emit(doc.sha1);
  }
};