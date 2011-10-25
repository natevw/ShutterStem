function (head, req) {
    var ddoc = this;
    var fs = require('lib/flatstache');
    provides("html", function () {
        var app_url = fs.to_html("/{{{db}}}/{{{id}}}", {db:req.info.db_name, id:ddoc._id});
        var row, baskets = "", template = "<li id='{{id}}'><a href='{{app_url}}/_show/basket/{{id}}'>{{ name }}</a> ({{ photoCount }})</li>";
        while (row = getRow()) {
            baskets += fs.to_html(template, {app_url:app_url, id:row.id, name:row.value.name, photoCount:''+row.value.photoCount});
        }
        return fs.to_html(ddoc.templates.baskets, {baskets:baskets});
    });
}
