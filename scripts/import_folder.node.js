var import_source = {
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


var import_queue = new Serializer(function (fullpath, finish) {
    var get_photo = proc.spawn(GET_PHOTO, ['--thumbnail', '64', '--thumbnail', '256', '--timezone', import_source.time_zone, fullpath]);
    
    var imageDoc = "";
    get_photo.stdout.on('data', function (data) {
        imageDoc += data.toString();
    });
    get_photo.on('exit', function (exitCode) {
        if (exitCode !== 0) {
            finish();
            return;
        }
        var docName = "/dev/testphoto-" + Math.random();
        var req = couchdb.request('PUT', docName, {'Connection': 'keep-alive'});
        req.write(imageDoc);
        req.end();
        req.on('response', function (resp) {
           console.log("Imported", fullpath, "to", docName);
           finish();
        });
    });
});

processFiles(import_source.path, function (fullpath) {
    var extension = path.extname(fullpath).slice(1).toLowerCase();
    if (!SUPPORTED_EXTENSIONS[extension]) {
        return;
    }
    import_queue.add(fullpath);
});
