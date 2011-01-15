/* Simple workaround for older JavaScript engines that
 * do not understand the One True Date Format.
 * This doesn't totally mimic new Date(), just string parsing.
 */
exports.newDate = function (rfc3339) {
    var parts, date, time, MA;
    
	// ES5 conformant Date.parse can handle RFC3399 directly
	time = Date.parse(rfc3339);
	if (!isNaN(time)) {
		return new Date(time);
	}
    
	// Nasty RFC 822–style dates are well supported. So we convert, e.g.:
	// "2010-07-28T00:00:00.5Z" to "28 Jul 2010 00:00:00 GMT"
	// "2010-07-28T00:00:00.5-07:00" to "28 Jul 2010 00:00:00 -0700"
	// ...then add back millseconds
    
	parts = rfc3339.split("T");
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
		intSecs = intSecs.toFixed();
		return (intSecs.length == 2) ? intSecs + " " : "0" + intSecs + " ";
	});
    
	date = new Date(date + " " + time);
	date.setMilliseconds(parts * 1000);
	return date;
};

exports.toUTCComponents = function (date) {
	return [
		date.getUTCFullYear(),      // 0
		date.getUTCMonth() + 1,     // 1
		date.getUTCDate(),          // 2
		date.getUTCHours(),         // 3
		date.getUTCMinutes(),       // 4
		date.getUTCSeconds() + (date.getUTCMilliseconds() / 1000)
    ];
};

exports.toRFC3339 = function (date) {
    // after https://github.com/couchapp/couchapp/blob/master/vendor/lib/atom.js
    
    function f(n) {    // Format integers to have at least two digits.
        return n < 10 ? '0' + n : '' + n;
    }
    var d = exports.toUTCComponents(date);
    return d[0] + '-' + f(d[1]) + '-' + f(d[2]) + 'T' + f(d[3]) + ':' + f(d[4]) + ':' + f(d[5]) + 'Z'
};
