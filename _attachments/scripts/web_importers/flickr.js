var f = require('fermata'),
    Q = require('queue-async');
f.registerPlugin('flickr', require('fermata/plugins/flickr'));


var CREDS = {
    client: process.env.APP_KEY,
    client_secret: process.env.APP_SECRET,
    token: process.env.TOKEN,
    token_secret: process.env.SECRET
}, api = f.flickr(CREDS);

api.rest({method:"flickr.people.getPhotos", user_id:"me", privacy_filter:1}).get(function (e,d) {
    if (e) console.error(e.stack);
    else console.log(d.photos);
});