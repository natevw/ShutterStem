function (doc, req) {
	var path, mustache;
	// !json templates.photo_info
	
	path = require("vendor/couchapp/lib/path").init(req);
	mustache = require("vendor/couchapp/lib/mustache");
	
	provides("html", function () {
		doc.source = JSON.stringify(doc, null, 4);
		doc.thumbnail = {"medium": path.doc(doc._id, "medium.jpg") };
		if (!doc.name && doc.image && doc.image.original_filename) {
			doc.name = doc.image.original_filename;
		}
		return mustache.to_html(templates.photo_info, doc);
	});
};
