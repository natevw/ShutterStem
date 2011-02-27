function (doc, req) {
    var ddoc = this;
    provides("html", function () {
        if (req.query.random) {
            // avoid caching of csrf_token (a bit overzealous...?)
            return {code:400, body:"<h1>Bad Request</h1>You must include a random query parameter."};
        }
        
        doc || (doc = {});
        var host = "http://localhost:5984/";
        doc.database_url = host + req.info.db_name;
        doc.database_futon_url = host + "_utils/database.html?" + req.info.db_name;
        doc.csrf_token = '' + Math.round(Math.random() * 1e16) + req.uuid + Math.round(Math.random() * 1e16) + '';
        
        if (req.query.type === 'export') {
            doc.title = "Export " + (req.query.name || "images");
            doc.location_html = "your desired export destination";
            doc.frame_host = host;
            var query = "?name=" + req.query.name + "&token=" + doc.csrf_token + "&utility=";
            doc.frame_path = req.info.db_name + "/_design/shutterstem/_show/export" + query;
            doc.frame_message = req.query.images;
        }
        
        var html = require("lib/flatstache").to_html(ddoc.templates.utility, doc);
        //return {headers:{'Content-Disposition':"attachment"}, body:html};
        return html;
    });
}
