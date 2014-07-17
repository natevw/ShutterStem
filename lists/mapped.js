function (head, req) {
    var ddoc = this;
    var fs = require('lib/flatstache');
    provides("html", function () {
        var db_url = ('X-Forwarded-For' in req.headers) ? '' : ('/' + req.info.db_name),
            app_url = db_url + '/' + ddoc._id;
        if (!db_url) db_url = '/.';
        
        var row, lastRow, photos = [];
        while (row = getRow()) {
            photos.push({id:row.id, value:row.value});
            lastRow = row;
        }
        if (lastRow) photos[photos.length-1].key = lastRow.key;
        
        return fs.to_html(ddoc.templates.mapped, {
            //debug: JSON.stringify({ddoc:ddoc, head:head, req:req}, null, 4),
            db_url:db_url,
            app_url:app_url,
            photos:JSON.stringify(photos),
            query_limit: JSON.stringify(parseInt(req.query.limit) || null)
        });
    });
}
