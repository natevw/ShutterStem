function (doc, req) {
    var ddoc = this;
    provides("html", function () {
        if (0 && !req.query.random) {
            // avoid caching of csrf_token (a bit overzealous...?)
            return {code:400, body:"<h1>Bad Request</h1>You must include a random query parameter."};
        }
        doc.database_url = "http://localhost:5984/" + req.info.db_name;
        doc.database_futon_url = "http://localhost:5984/_utils/database.html?" + req.info.db_name;
        doc.csrf_token = '' + Math.round(Math.random() * 1e16) + req.uuid + Math.round(Math.random() * 1e16) + '';
        
        var html = require("lib/mustache").to_html(ddoc.templates.source_utility, doc);
        //return {headers:{'Content-Disposition':"attachment"}, body:html};
        return html;
    });
}
