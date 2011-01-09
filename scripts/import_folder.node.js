var REF_TYPE = "testtype-reference";
var SOURCE_TYPE = "testtype-source";
var IMAGE_TYPE = "testtype-image";
var PHOTO_TYPE = "testtype-photo";


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

function Serializer(callback) {
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
}

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

/*
var uuids;
var req = couchdb.request('GET', "/_uuids?count=1000", {'Connection': 'keep-alive'});
req.end();
req.on('response', function (resp) {
    var uuidsDoc = "";
    resp.setEncoding('utf8');
    resp.on('data', function (d) {
        uuidsDoc += d;
    });
    resp.on('end', function () {
        uuids = JSON.parse(uuidsDoc).uuids;
    });
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

var import_queue = new Serializer(function (info, finish) {
    var fullpath = path.join(info.folder, info.file);
    var get_photo = proc.spawn(GET_PHOTO, ['--thumbnail', '64', '--thumbnail', '512', '--timezone', import_source.time_zone, fullpath]);
    
    var imageDoc = "";
    get_photo.stdout.on('data', function (data) {
        imageDoc += data.toString();
    });
    get_photo.on('exit', function (exitCode) {
        if (exitCode !== 0) {
            finish();
            return;
        }
        imageDoc = JSON.parse(imageDoc);
        imageDoc.identifiers || (imageDoc.identifiers = {});
        imageDoc.identifiers.relative_path = {source:makeRef(import_source, ['name']), file:info.file};
        var docName = "/dev/testphoto-" + Math.random();
        var req = couchdb.request('PUT', docName, {'Connection': 'keep-alive'});
        req.write(JSON.stringify(imageDoc));
        req.end();
        req.on('response', function (resp) {
           console.log("Imported", fullpath, "to", docName);
           finish();
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
