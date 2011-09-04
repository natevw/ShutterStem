function (doc, req) {
    default xml namespace = "http://www.topografix.com/GPX/1/0";
    req.body = req.body.replace("<?xml version=\"1.0\"?>", "");  // see https://developer.mozilla.org/en/e4x
    
    var file = new XML(req.body),
        locs = [];
    for each (p in file..trkpt) {
        locs.push({
            lat: Number(p.@lat),
            lon: Number(p.@lon),
            ele: Number(p.ele.text()),
            time: String(p.time.text())
        });
    }
    return [null, {json:locs}];
}