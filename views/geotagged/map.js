function (doc) {
    var IMAGE_TYPE = "com.shutterstem.image";
    if (!doc[IMAGE_TYPE]) return;
    if (!doc.geotag) return;
    
    function coordToQuadkey(coord, ZOOM_LEVEL) {
        var NBITS = Math.min(ZOOM_LEVEL || 32, 32),     // NBITS must be 32 or below for JS bitwise operators
            NTILES = Math.pow(2, NBITS),
            x = (coord.lon + 180) / 360,
            l = Math.sin(coord.lat * Math.PI / 180),
            y = 0.5 - Math.log((1 + l) / (1 - l)) / (4 * Math.PI),
            tx = x * NTILES, ty = y * NTILES;
        
        var quads = [], nshifts = NBITS;
        while (nshifts --> 0) {
            quads.push((ty & 1) * 2 + (tx & 1));
            tx = tx >>> 1, ty = ty >>> 1;
        }
        return quads.reverse();
    }
    emit(coordToQuadkey(doc.geotag), doc.geotag);
}
