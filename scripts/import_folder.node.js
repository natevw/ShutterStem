var import_source = {
    path: "/Users/nathan/Pictures/elgar_digipics",
    last_import: null
}

var SUPPORTED_EXTENSIONS = {'jpg':true, 'jpeg':true};


var fs = require('fs');
var path = require('path');


function processFiles(folder, callback) {
    fs.readdir(folder, function (e, files) {
        if (e) {
            console.warn(e);
            return;
        }
        
        files.forEach(function (filename) {
            if (filename[0] === '.') {
                return;
            }
            
            var fullpath = path.join(folder, filename);
            fs.stat(fullpath, function (e, stats) {
                if (e) {
                    console.warn(e);
                    return;
                }
                
                if (stats.isDirectory()) {
                    processFiles(fullpath, callback);
                } else {
                    callback(fullpath);
                }
            });
        });
    });
}

processFiles(import_source.path, function (fullpath) {
    var extension = path.extname(fullpath).slice(1).toLowerCase();
    if (!SUPPORTED_EXTENSIONS[extension]) {
        return;
    }
    console.log(fullpath);
});
