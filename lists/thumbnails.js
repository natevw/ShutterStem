function (head, req) {
    var ddoc = this;
    provides("html", function () {
        var Mustache = require("lib/mustache");
        var list = require("lib/list");
        
        var image = list.rows();
        var num_prev = head.offset;
        var num_next = (req.query.limit) ? Math.max(0, head.total_rows - (head.offset + req.query.limit)) : 0;
        var SIZE = 256, PAD_LIMIT = 8167;
        var data = {
            pad_above: Math.min(num_prev * SIZE, PAD_LIMIT),
            pad_below: Math.min(num_next * SIZE, PAD_LIMIT),
            image: image,
            first_image: image.first(JSON.stringify),
            last_image: image.last(JSON.stringify),
            thumbnail_partial: ddoc.templates.partials.thumbnail
        };
        return Mustache.to_html(ddoc.templates.thumbnails, data, ddoc.templates.partials);
    });
}
