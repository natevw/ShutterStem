#! /Users/nathan/sw/bin/node
//#! /usr/bin/env node

// see http://wiki.apache.org/couchdb/ExternalProcesses for configuration instructions

var fs = require('fs');

process.stdin.resume();
process.stdin.setEncoding('utf8');

var lineBuffer = "";
process.stdin.on('data', function (chunk) {
    var lines = (lineBuffer + chunk).split("\n");
    lineBuffer = lines.pop();
    lines.forEach(function (line) {
        var request = JSON.parse(line);
        
        var dbname = request.path[0];
        var import_id = request.path[2];
        
        // POST /dev/_import/test {helper_path:"", csrf_token:""}  -> start/conflict
        if (request.method === 'POST') {
            // check helper_path for csrf_token
            if (!request.query.csrf_token) {
                // TODO
            }
            
            var ticket = "<!-- SHUTTERSTEM-TOKEN(" + request.query.csrf_token + ")TOKEN-SHUTTERSTEM -->";
            try {
                var fd = fs.openSync(request.query.helper_path, 'r');
                fs.readSync(fd, 4096, 0, "utf-8");
            } except (e) {
            
            }
            
            
            // BAH WHAT A MESS 
            
            
            
            fs.createReadStream(, {flags:'r', encoding:"utf-8", end:},
            var helperContents = fs.readFileSync(, "utf-8");
            if (helperContents.indexOf(ticket) === -1) {
                
            }
            
            // make sure import isn't already in progress
            
            // start import
        }
        
        
        
        
        
        // GET /dev/_import/test    -> status
        
        
        process.stdout.write(JSON.stringify({body:"<h1>Hello World!</h1>\n<pre>\n" + JSON.stringify(request, null, 4) + "</pre>"}) + '\n');
        process.stdout.flush();
    });
});
