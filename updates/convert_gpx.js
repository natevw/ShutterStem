function (doc, req) {
    log("HERE 0");
    req.body = req.body.replace(/^<\?xml .*?>/, "");    // see https://developer.mozilla.org/en/e4x
    log("HERE 1");
    var file = new XML(req.body),
        locs = [];
    log("HERE 2");
    for each (p in file..*::trkpt) {
        locs.push({
            lat: Number(p.@lat),
            lon: Number(p.@lon),
            ele: Number(p.*::ele.text()),
            time: String(p.*::time.text())
        });
    }
    return [null, {json:locs}];
}