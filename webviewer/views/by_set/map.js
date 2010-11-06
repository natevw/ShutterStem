function (doc) {
	if (!doc.sets) {
		return;
	}
	
	doc.sets.forEach(function (set) {
		emit(set);
	});
};
