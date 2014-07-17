var _ = require("./_common.js"),
    f = require('fermata'),
    Q = require('queue-async');
f.registerPlugin('flickr', require('fermata/plugins/flickr'));

var CREDS = {
    client: process.env.APP_KEY,
    client_secret: process.env.APP_SECRET,
    token: process.env.TOKEN,
    token_secret: process.env.SECRET
}, api = f.flickr(CREDS);

var INFO = ['description', 'date_taken', 'geo', 'tags'/*, 'url_z', 'url_t'*/],
    SIZE = {smSq75:'s',lgSq150:'q',thumb100:'t',sm240:'m',sm320:'n',med500:'-',med640:'z',med800:'c',lg1024:'b',orig:'o'},
    ACC = {world:1, country:3, region:6, city:11, street:16};   // basically, equivalent to slippy map zoom level?

function photoURL(d,s) {    // see https://www.flickr.com/services/api/misc.urls.html
    return f.json("https://farm"+d.farm+".staticflickr.com/"+d.server+"/"+d.id+"_"+d.secret+"_"+SIZE[s]+".jpg");
}

function meters(acc) {      // fudgy, see https://www.flickr.com/services/api/flickr.photos.geo.setLocation.html
    return 6378137 / Math.pow(2,acc+2);
}

_.fetchPhoto = function (d, cb) {
    var doc = {},
        q = Q();
    console.log("Fetching", d.id);
    q.defer(_.apply, photoURL(d,'thumb100').get, {Accept:"image/jpeg"}, Buffer(0));
    q.defer(_.apply, photoURL(d,'med640').get, {Accept:"image/jpeg"}, Buffer(0));
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
};

var enqueuePage = _.retry.bind(function (n, cb) {
    console.log("Fetching page", n, "of photos.");
    api.rest({
        method:"flickr.people.getPhotos",
        user_id:"me", privacy_filter:1,
        extras:INFO.join(','), page:n
    }).get(function (e,d) {
        if (e) return cb(e);
        else d = d.photos;
        
        d.photo.forEach(function (p) {
            q.defer(_.processPhoto, p);
        });
        if (n < d.pages) q.defer(enqueuePage, n+1);
        cb();
    });
});

var q = Q(1);
q.defer(enqueuePage, 1);
q.awaitAll(function (e) {
    if (e) console.error(e.stack);
    else console.log("All done!");
});
