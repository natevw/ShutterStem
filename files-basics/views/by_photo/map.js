function(doc) {
  if (doc.photo) {
    emit(doc.photo);
  }
};