#! /Users/nathan/sw/bin/node
//#! /usr/bin/env node

// see http://wiki.apache.org/couchdb/ExternalProcesses for configuration instructions

process.stdin.resume();
process.stdin.setEncoding('utf8');

var lineBuffer = "";
process.stdin.on('data', function (chunk) {
    var lines = (lineBuffer + chunk).split("\n");
    lineBuffer = lines.pop();
    lines.forEach(function (line) {
        var request = JSON.parse(line);
        process.stdout.write(JSON.stringify({code: 200, headers:{'content-type':'text/html'}, body:"<h1>Hello World!</h1>\n<pre>\n" + JSON.stringify(request, null, 4) + "</pre>"}) + '\n');
        process.stdout.flush();
    });
});
