var f = require('fermata'),
    Q = require('queue-async');
f.registerPlugin('flickr', require('fermata/plugins/flickr'));

var CREDS = {
    client: process.env.APP_KEY,
    client_secret: process.env.APP_SECRET,
    token: process.env.TOKEN,
    token_secret: process.env.SECRET
}, api = f.flickr(CREDS), db = f.json(process.env.DB_URL);

var INFO = ['description', 'date_taken', 'geo', 'tags'/*, 'url_z', 'url_t'*/],
    SIZE = {smSq75:'s',lgSq150:'q',thumb100:'t',sm240:'m',sm320:'n',med500:'-',med640:'z',med800:'c',lg1024:'b',orig:'o'},
    ACC = {world:1, country:3, region:6, city:11, street:16};   // basically, equivalent to slippy map zoom level?

// WORKAROUND: https://github.com/natevw/fermata/issues/28
// NOTE: breaks unless run with `node --harmony_proxies`
function _apply(fn) {
    var args = Array.prototype.slice.call(arguments, 1);
    return Function.prototype.apply.call(fn, this, args);
}

function photoURL(d,s) {    // see https://www.flickr.com/services/api/misc.urls.html
    return f.json("https://farm"+d.farm+".staticflickr.com/"+d.server+"/"+d.id+"_"+d.secret+"_"+SIZE[s]+".jpg");
}

function meters(acc) {      // fudgy, see https://www.flickr.com/services/api/flickr.photos.geo.setLocation.html
    return 6378137 / Math.pow(2,acc+2);
}

function fetchPhoto(d, cb) {
    var doc = {},
        q = Q();
    console.log("Fetching", d.id);
    q.defer(_apply, photoURL(d,'thumb100').get, {Accept:"image/jpeg"}, Buffer(0));
    q.defer(_apply, photoURL(d,'med640').get, {Accept:"image/jpeg"}, Buffer(0));
    q.await(function (e,sm,lg) {
        if (e) cb(e);
        else cb(null, {
            "com.shutterstem.image": true,
            identifiers: {
                flickr: {id:d.id}
            },
            timestamp: d.datetaken.replace(' ','T'),        // see https://www.flickr.com/services/api/misc.dates.html
            geotag: (d.accuracy) ? {lat:d.latitude, lon:d.longitude, acc:meters(d.accuracy)} : void 0,
            dbg_flickr: {title:d.title, description:d.description, geo_accuracy:d.accuracy},
            _attachments: {
                "thumbnail/512.jpg": {content_type: "image/jpeg", data:lg.toString('base64')},
                "thumbnail/64.jpg": {content_type: "image/jpeg", data:sm.toString('base64')}
            }
        });
    });
}

function _processPhoto(photo, cb) {
    fetchPhoto(photo, function (e,d) {
        if (e) cb(e);
        else db.post(d, function (e,d) {
            if (e) cb(e);
            else console.log(" -> saved as", d.id), cb();
        });
    });
}

function processPhoto(photo, cb) {
    _processPhoto(photo, function (e) {
        if (e) {
            console.warn("Failed, retrying!");
            processPhoto(photo, cb);
        } else cb.apply(this, arguments);
    });
}

api.rest({method:"flickr.people.getPhotos", user_id:"me", privacy_filter:1, extras:INFO.join(',')}).get(function (e,d) {
    if (e) console.error(e.stack);
    else console.log(d.photos, d.photos.photo[0].description._content);
    
    // TODO: pagination
    var q = Q(1);
    d.photos.photo.forEach(function (d) {
        q.defer(processPhoto, d);
    });
    q.awaitAll(function (e) {
    
    });
});