function (doc) {
	var digest = doc.image && doc.image.original_sha1;
	if (digest) {
		emit(digest);
	}
};
