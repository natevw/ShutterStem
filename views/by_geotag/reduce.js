function (keys, values, redux) {
    var s = values.reduce((redux) ? function (summed, avg) {
        summed.lat += avg.lat * avg.count;
        summed.lon += avg.lon * avg.count;
        summed.n += avg.count;
        return summed;
    } : function (summed, loc) {
        summed.lat += loc.lat;
        summed.lon += loc.lon;
        summed.n += 1;
        return summed;
    }, {lat:0, lon:0, n:0});
    return {lat:s.lat/s.n, lon:s.lon/s.n, count:s.n};
}