function (head, req) {
    var ddoc = this;
    var fs = require('lib/flatstache');
    provides("html", function () {
        return fs.to_html(ddoc.templates.thumbnails, {
            app_url: fs.to_html("/{{{db}}}/{{{id}}}", {db:req.info.db_name, id:ddoc._id}),
            //debug: JSON.stringify({ddoc:ddoc, head:head, req:req}, null, 4)
        });
    });
}
