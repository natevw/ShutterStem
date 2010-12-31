var import_source = {
    path: "/Users/nathan/Pictures/elgar_digipics",
    last_import: null
}

var SUPPORTED_EXTENSIONS = {'jpg':true, 'jpeg':true};


var fs = require('fs'), path = require('path'), proc = require('child_process');

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


var import_queue = new Serializer(function (fullpath, finish) {
    //console.log(fullpath);
    var sips = proc.spawn("sips", ['-g', 'creation', fullpath]);
    
    var output = "";
    sips.stdout.on('data', function (data) {
        output += data.toString();
    });
    sips.on('exit', function () {
        var date = output.split("\n")[1].match("creation: (.*)$")[1];
        if (date === "<nil>") {
            finish();
            return;
        }
        
        date = date.replace(/(\d+):(\d+):(\d+) /, "$1-$2-$3T");
        if (import_source.gmt) {
            date += 'Z';
        } else {
            // NOTE: this takes advantage of V8 parsing zoneless timestamps as local
            var local_date = new Date(date);
            var gmt_date = new Date(date + 'Z');
            var seconds_offset = (gmt_date - local_date) / 1000;
            var minutes_offset = Math.abs(seconds_offset) / 60;
            var hours_offset = Math.floor(minutes_offset / 60)
            minutes_offset = Math.round(minutes_offset - hours_offset * 60);
            date += (seconds_offset > 0) ? '+' : '-';
            date += (hours_offset < 10) ? '0' + hours_offset : '' + hours_offset;
            date += ':';
            date += (minutes_offset < 10) ? '0' + minutes_offset : '' + minutes_offset;
        }
        console.log(fullpath, date);
        finish();
    });
});

processFiles(import_source.path, function (fullpath) {
    var extension = path.extname(fullpath).slice(1).toLowerCase();
    if (!SUPPORTED_EXTENSIONS[extension]) {
        return;
    }
    import_queue.add(fullpath);
});
