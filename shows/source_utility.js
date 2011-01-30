function (doc, req) {
    var ddoc = this;
    provides("html", function () {
        var Mustache = require("lib/mustache");
        
        doc.database_url = "http://localhost:5984/" + req.info.db_name;
        doc.database_futon_url = "http://localhost:5984/_utils/database.html?" + req.info.db_name;
        
        var html = Mustache.to_html(ddoc.templates.source_utility, doc);
        //return {headers:{'Content-Disposition':"attachment"}, body:html};
        return html;
    });
}
