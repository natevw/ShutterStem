var REF_TYPE = "testtype-reference";
var SOURCE_TYPE = "testtype-source";
var IMAGE_TYPE = "testtype-image";
var PHOTO_TYPE = "testtype-photo";      // plan to separate concept of image and photo


var import_source = {
    _id: "testsource-elgar_digipics",
    _rev: "testrev",
    name: "Elgar pictures",
    path: "/Users/nathan/Pictures/elgar_digipics",
    last_import: null,
    time_zone: 'US/Pacific'
};

var SUPPORTED_EXTENSIONS = {'jpg':true, 'jpeg':true};
var GET_PHOTO = __dirname + '/getphoto-osx/build/Release/getphoto';

var fs = require('fs'), path = require('path'), proc = require('child_process'), http = require('http');

function Serial(){};
Serial.any = function (array, test, finish) {
    var i = 0, len = array.length, value;
    function next() {
        if (i < len) {
            return test(array[i], function (retValue) {
                i += 1;
                value = retValue;
                if (!value) {
                    // avoid deep stack of "return next();" by queuing instead
                    return process.nextTick(next);
                } else {
                    return finish(value);
                }
            });
        } else {
            return finish(value);
        }
    }
    next();
};
Serial.izer = function (callback) {
    var queue = [];
    var tick = function () {
        process.nextTick(nextItem);
    };
    var nextItem = function () {
        if (!queue.length) {
            return;
        }
        callback(queue.shift(), tick);
    }
    this.add = function (item) {
        if (!queue.length) {
            tick();
        }
        queue.push(item);
    }
};

function processFiles(base, subfolder, callback) {
    var folder = path.join(base, subfolder);
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
                
                var subfile = path.join(subfolder, filename);
                if (stats.isDirectory()) {
                    processFiles(base, subfile, callback);
                } else {
                    callback(base, subfile);
                }
            });
        });
    });
}


var couchdb = require('http').createClient(5984, "localhost");
couchdb.get = function (path, sendDoc) {
    var req = couchdb.request('GET', path);
    req.end();
    req.on('response', function (resp) {
        var doc = "";
        resp.setEncoding('utf8');
        resp.on('data', function (d) {
            doc += d;
        });
        resp.on('end', function () {
            sendDoc(JSON.parse(doc));
        });
    });
}

/*
couchdb.get("/_uuids?count=1", function (result) {
    console.log(JSON.stringify(result.uuids));
});
*/

function makeRef(doc, denormalize) {
    var reference = {};
    reference[REF_TYPE] = true;
    reference._id = doc._id;
    if (denormalize) denormalize.forEach(function (field) {
        reference[field] = doc[field];
    }), (reference._rev = doc._rev);
    return reference;
}

var import_queue = new Serial.izer(function (info, finishInfo) {
    var fullpath = path.join(info.folder, info.file);
    var get_photo = proc.spawn(GET_PHOTO, ['--thumbnail', '64', '--thumbnail', '512', '--timezone', import_source.time_zone, fullpath]);
    
    var imageDoc = "";
    get_photo.stdout.on('data', function (data) {
        imageDoc += data.toString();
    });
    get_photo.on('exit', function (exitCode) {
        if (exitCode !== 0) {
            console.warn("Error processing", fullpath);
            return finishInfo();
        }
        imageDoc = JSON.parse(imageDoc);
        imageDoc[IMAGE_TYPE] = true;
        imageDoc.identifiers || (imageDoc.identifiers = {});
        imageDoc.identifiers.relative_path = {source:makeRef(import_source, ['name']), path:info.file};
        
        Serial.any(Object.keys(imageDoc.identifiers), function (identifierName, finishIdentifier) {
            var identifier = imageDoc.identifiers[identifierName];
            var key;
            if (identifierName === "relative_path") {
                key = [identifier.source._id, identifier.path];
            } else {
                key = identifier;
            }
            couchdb.get("/dev/_design/shutterstem/_view/by_identifier?key=" + encodeURIComponent(JSON.stringify(key)), function (identifierDocs) {
                return finishIdentifier(identifierDocs.rows.length ? true : false);
            });
        }, function (exists) {
            if (exists) {
                console.log("Skipping", fullpath);
                return finishInfo();
            }
            
            var docName = "/dev/testphoto-" + Math.random();
            var req = couchdb.request('PUT', docName, {'Connection': 'keep-alive'});
            req.write(JSON.stringify(imageDoc));
            req.end();
            req.on('response', function (resp) {
               console.log("Imported", fullpath, "to", docName);
               return finishInfo();
            });
        });
    });
});

processFiles(import_source.path, null, function (folder, file) {
    var extension = path.extname(file).slice(1).toLowerCase();
    if (!SUPPORTED_EXTENSIONS[extension]) {
        return;
    }
    import_queue.add({folder:folder, file:file});
});
