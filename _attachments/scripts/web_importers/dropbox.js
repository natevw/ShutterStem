var f = require('fermata'),
    Q = require('queue-async');


function makeSet(arr) {
    return arr.reduce(function (obj, k) {
        obj[k] = true;
        return obj;
    }, Object.create(null))
}

var CONTENT = makeSet(['files', 'thumbnails', 'previews', 'files_put', 'chunked_upload', 'commit_chunked_upload']),
    NO_AUTO = makeSet(['account', 'delta', 'longpoll_delta', 'chunked_upload', 'fileops']);

f.registerPlugin('dropbox', function (transport, key) {
    this.base = "/1/";       // (placeholder)
    this.path = [];
    transport = transport.using('statusCheck').using('autoConvert', "application/json");
    
    return function (req, callback) {
        // TODO: this check is not production-grade, and there are a couple subdomains missing
        if (req.path[0] in CONTENT) req.base = "https://api-content.dropbox.com/1/";
        else req.base = "https://api.dropbox.com/1/";
        
        // HACK: allow elision of common "auto" path component
        if (req.path[0] in NO_AUTO || req.path[1] === 'auto') ;
        else req.path.splice(1, 0, 'auto');
        
        // via https://www.dropbox.com/developers/blog/45/using-oauth-20-with-the-core-api
        req.headers['Authorization'] = "Bearer "+key;
        
        return transport(req, callback);
    };
});


var api = f.dropbox(process.env.API_TOKEN),
    db = f.json(process.env.DB_URL);

function logback(e,d) {
    if (e) throw e;
    else console.log(d);
}

//api.account.info.get(logback);


// WORKAROUND: https://github.com/natevw/fermata/issues/28
// NOTE: breaks unless run with `node --harmony_proxies`
function _apply(fn) {
    var args = Array.prototype.slice.call(arguments, 1);
    return Function.prototype.apply.call(fn, this, args);
}

function fetchPhoto(path, cb) {
    var doc = {},
        q = Q();
    q.defer(_apply, api.metadata([path], {include_media_info:true}).get);
    q.defer(_apply, api.thumbnails([path], {size:'s'}).get, {Accept:"image/jpeg"}, Buffer(0));
    q.defer(_apply, api.thumbnails([path], {size:'l'}).get, {Accept:"image/jpeg"}, Buffer(0));
    //q.defer(_apply, api.files([path]).head, {Accept:"*/*"}, Buffer(0));
    
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
}

function processPhoto(path, cb) {
    fetchPhoto(path, function (e,d) {
        if (e) cb(e);
        else db.post(d, cb);
    });
}

processPhoto('/10000/_DSC0012.jpg', logback);


//api.files(['/10000/_DSC0012.jpg']).get({Accept:"*/*"}, Buffer(0), function (e,d,m) {
//    console.log("META", e,d,m);
//    var md5 = require('crypto').createHash('md5'),
//        sha = require('crypto').createHash('sha1');
//    md5.update(d), sha.update(d);
//    md5 = md5.digest(), sha = sha.digest();
//    console.log("MD5", md5.toString('hex'), md5.toString('base64'));
//    console.log("SHA1", sha.toString('hex'), sha.toString('base64'));
//    // NOTE: neither of these seem to be exposed in Dropbox metadata
//});

/*
api.metadata.auto(['10000'], {include_media_info:true}).get(function (e,d) {
    if (e) throw e;
    
    var q = Q(1);
    d.contents.forEach(function (file) {
        q.defer(processPhoto, file, db);  
    })
    q.awaitAll(function (e,arr) {
        if (e) throw e;
        console.log("Processed results, count:", arr.length);
    });
    
    console.log("# files:", d.contents.length);
    console.log(d.contents[0]);
});
*/