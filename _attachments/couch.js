function Couch(url) {
    this.url = url;
}
Couch.prototype.urlFor = function (path, query) {
    if (path.join) {
        path = path.join("/");
    }
    if (query) {
        path += "?" + Object.keys(query).map(function (key) {
            if (key[0] === '$') {
                return encodeURIComponent(key.slice(1)) + "=" + encodeURIComponent(JSON.stringify(query[key]));
            } else {
                return encodeURIComponent(key) + "=" + encodeURIComponent(query[key]);
            }
        }).join("&");
    }
    return this.url + "/" + path;
};
Couch.prototype.http = function (method, obj, path, query, callback) {
    var req = new XMLHttpRequest();
    req.open(method, this.urlFor(path, query));
    req.setRequestHeader("Content-Type", "application/json");
    req.send(JSON.stringify(obj));
    req.onreadystatechange = function() {
        if (req.readyState === req.DONE) {
            callback(req.status, JSON.parse(req.responseText));
        }
    }
};
Couch.prototype.get = function (path, query, callback) {
    this.http("GET", null, path, query, function (status, result) {
        callback((status === 200) ? result : null);
    });
};
