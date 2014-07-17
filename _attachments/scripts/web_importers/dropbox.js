var _ = require("./_common.js"),
    f = require('fermata'),
    Q = require('queue-async');
f.registerPlugin('dropbox', require("./fermata-dropbox.js"));

var api = f.dropbox(process.env.API_TOKEN),
    folder = process.env.FOLDER;

_.fetchPhoto = function (path, cb) {
    var doc = {},
        q = Q();
    if (typeof path === 'object') {
        q.defer(function (d, cb) { cb(null, d); }, path);
        path = path.path;
    } else q.defer(_.apply, api.metadata([path], {include_media_info:true}).get);
    console.log("Fetching", path);
    
    q.defer(_.apply, api.thumbnails([path], {size:'s'}).get, {Accept:"image/jpeg"}, Buffer(0));
    q.defer(_.apply, api.thumbnails([path], {size:'l'}).get, {Accept:"image/jpeg"}, Buffer(0));
    q.await(function (e,d,sm,lg) {
        if (e) cb(e);
        else if (typeof d.photo_info !== 'object') cb(new Error("Photo metadata not available: "+meta.photo_info));  // e.g. 'pending'
        else cb(null, {
            "com.shutterstem.image": true,
            identifiers: {
                path: {
                    source: {_id:"imgsrc-DROPBOX_DEMO","net.stemstorage.reference":true},
                    name: d.path.slice(1), dbg_size: d.bytes
                }
            },
            timestamp: new Date(d.photo_info.time_taken).toISOString(),
            geotag: (d.photo_info.lat_long) ? {lat:d.photo_info.lat_long[0], lon:d.photo_info.lat_long[1]} : void 0,
            _attachments: {
                "thumbnail/512.jpg": {content_type: "image/jpeg", data:lg.toString('base64')},
                "thumbnail/64.jpg": {content_type: "image/jpeg", data:sm.toString('base64')}
            }
        });
    });
};

console.log("Fetching contents of Dropbox folder:", folder);
_.retry.bind(function (cb) {
    api.metadata([folder], {include_media_info:true}).get(function (e,d) {
        if (e) return cb(e);
        
        console.log("Folder contains", d.contents.length, "files");
        
        var q = Q(1);
        d.contents.forEach(function (file) {
            // TODO: handle non-photos, subfolders…
            q.defer(_.processPhoto, file);  
        });
        q.awaitAll(cb);
    });
})(function (e,arr) {
    if (e) console.error(e.stack);
    else console.log("Success!");
});
