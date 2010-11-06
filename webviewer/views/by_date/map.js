function(doc) {
	if (!doc.timestamp) return;
	
	// !code lib/date.js
	
	emit(toComponentsUTC(dateFromRFC3399(doc.timestamp)));
}
