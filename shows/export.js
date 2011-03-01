function (doc, req) {
    var ddoc = this;
    provides("html", function () {
        doc || (doc = {});
        doc.database_url = "http://localhost:5984/" + req.info.db_name;
        doc.utility_path = req.query.utility;
        doc.csrf_token = req.query.token;
        doc.default_subfolder_name = req.query.name;
        return require("lib/flatstache").to_html(ddoc.templates['export'], doc);
    });
}
