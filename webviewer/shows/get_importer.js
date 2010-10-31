function (doc, req) {
	var mustache, templates, db_url;
	
	mustache = require("vendor/couchapp/lib/mustache");
	// !json templates.iphoto_import
	
	db_url = ["http:/", req.headers['Host'], req.info.db_name].join('/');
	return {
		'body': mustache.to_html(templates.iphoto_import, {database:db_url}),
		'headers': {
			"Content-Type" : "text/html",
			"Content-Disposition" : "attachment; filename=ShutterStem iPhoto importer.html",
		}
	};
};
