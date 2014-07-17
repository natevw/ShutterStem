function (doc, req) {
    var ddoc = this;
    var fs = require('lib/flatstache');
    provides("html", function () {
        var db_url = ('X-Forwarded-For' in req.headers) ? '' : ('/' + req.info.db_name),
            app_url = fs.to_html("{{{db_url}}}/{{{id}}}", {db_url:db_url, id:ddoc._id});
        if (!db_url) db_url = '/.';
        var photos = "", template = "<img id='{{id}}' class='photo' src='{{{db}}}/{{{id}}}/thumbnail/64.jpg'>";
        if (!doc) doc = {
            'com.shutterstem.basket': true,
            name: "New Basket",
            photos: []
        };
        doc.photos.forEach(function (photoRef) {
            photos += fs.to_html(template, {db:db_url, id:photoRef._id});
        });
        return fs.to_html(ddoc.templates.basket, {
            db_url:db_url, app_url:app_url, name:doc.name,
            doc_source: JSON.stringify(doc),
            photoCount:''+doc.photos.length, photos:photos
        });
    });
}
