function (head, req) {
    var ddoc = this;
    var fs = require('lib/flatstache');
    provides("html", function () {
        var app_url = ('X-Forwarded-For' in req.headers) ?
            fs.to_html("/{{{id}}}", {id:ddoc._id}) :
            fs.to_html("/{{{db}}}/{{{id}}}", {db:req.info.db_name, id:ddoc._id});
        
        var photoRow,
            thumbnails = "",
            thumbnailTemplate = "<div class='frame' id='{{id}}'><img class='image' src='{{app_url}}/../../{{id}}/thumbnail/512.jpg'></div>";
        while (photoRow = getRow()) {
            thumbnails += fs.to_html(thumbnailTemplate, {app_url:app_url, id:photoRow.id});
        }
        
        
        return fs.to_html(ddoc.templates.thumbnails, {
            app_url: app_url,
            thumbnails: thumbnails,
            //debug: JSON.stringify({ddoc:ddoc, head:head, req:req}, null, 4)
        });
    });
}
