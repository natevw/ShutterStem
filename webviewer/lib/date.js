function dateFromRFC3399(rfc3399) {
	var parts, date, time, MA;
	
	// ES5 conformant Date.parse can handle RFC3399 directly
	time = Date.parse(rfc3399);
	if (!isNaN(time)) {
		return new Date(time);
	}
	
	
	/* The following is fairly insane approach, converting first to the deprecated date format recognition */
	
	// "2010-07-28T00:00:00.5Z" to "28 Jul 2010 00:00:01 GMT"
	// "2010-07-28T00:00:00.5-07:00" to "28 Jul 2010 00:00:01 GMT"

	parts = rfc3399.split("T");
	date = parts[0];
	time = parts[1];

	parts = date.split("-").map(function (n) {
		return parseInt(n, 10);
	});
	MA = ["Month abbreviations",
		"Jan", "Feb", "Mar", "Apr",
		"May", "Jun", "Jul", "Aug",
		"Sep", "Oct", "Nov", "Dec"];
	date = [parts[2], MA[parts[1]], parts[0]].join(" ");

	time = time.replace("Z", " GMT");
	time = time.replace(/([+-])(\d\d):(\d\d)$/, " $1$2$3");
	parts = 0;
	time = time.replace(/[0-9]{2}\.[0-9]+ /, function (m) {
		var intSecs = parseInt(m);
		parts = parseFloat(m) - intSecs;
		var intSecs = intSecs.toFixed();
		return (intSecs.length == 2) ? intSecs + " " : "0" + intSecs + " ";
	});

	date = new Date(date + " " + time);
	date.setMilliseconds(parts * 1000);
	return date;
}

function toComponentsUTC(date) {
	return [
		date.getUTCFullYear(),
		date.getUTCMonth() + 1,
		date.getUTCDate() + 1,
		date.getUTCHours(),
		date.getUTCMinutes(),
		date.getUTCSeconds() + (date.getUTCMilliseconds() / 1000)];
}
