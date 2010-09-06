function (head, req) {
	var path, mustache;
	// !json templates.thumbnails
	
	path = require("vendor/couchapp/lib/path").init(req);
	mustache = require("vendor/couchapp/lib/mustache");
		
	provides("html", function () {
		var contents, view_name, list_name, row, link;
		
		contents = {
			photos: [],
			info: JSON.stringify(req)
		};
		
		list_name = req.path[4];
		view_name = req.path[5];
		
		// TODO: use iterator function instead
		while (row = getRow()) {
			link = (path.show("photo_info", row.id) + "?via_view=" + view_name +
					"&via_key=" + JSON.stringify(row.key) + "&from_list=" + list_name);
			contents.photos.push({
				link: link,
				name: "TODO",
				src: path.doc(row.id, "small.jpg")
			});
			
			if (!contents.first_key) {
				contents.first_key = row.key;
				contents.first_docid = row.id;
			} else {
				contents.last_key = row.key;
				contents.last_docid = row.id;
			}
		}
		
		
		link = {reduce:false, descending:true};
		if (req.query.limit) {
			link.limit = req.query.limit;
		}
		if (contents.last_key) {
			link.startkey = contents.last_key;
			link.startkey_docid = contents.last_docid;
		} else {
			contents.nextRestarts = true;
		}
		contents.nextLink = path.list(list_name, view_name, link);
		contents.first_key = JSON.stringify(contents.first_key);
		contents.last_key = JSON.stringify(contents.last_key);
		
		mustache.to_html(templates.thumbnails, contents, null, function(chunk) {
			send(chunk + "\n");
		});
	});
};
