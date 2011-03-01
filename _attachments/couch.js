function Couch(url) {
    this.url = url || Couch.guessDB();
}
Couch.prototype.urlFor = function (path, query) {
    if (path.join) {
        path = path.join("/");
    }
    if (query) {
        path += "?" + Couch._keys(query).map(function (key) {
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
    req.open(method, this.urlFor(path, query), Boolean(callback));
    req.setRequestHeader("Content-Type", "application/json");
    req.send(JSON.stringify(obj));
    if (callback) {
        req.onreadystatechange = function() {
            if (req.readyState === (req.DONE || 4)) {
                callback(req.status, JSON.parse(req.responseText));
            }
        }
    } else {
        req.response = JSON.parse(req.responseText);
    }
    return req;
};
Couch.prototype.get = function (path, query, callback) {
    if (callback) {
        this.http("GET", null, path, query, function (status, result) {
            callback((status === 200) ? result : null);
        });
    } else {
        var req = this.http("GET", null, path, query);
        return (req.status === 200) ? req.response : null;
    }
};

Couch.prototype.read = function (id) {
    var req = this.http("GET", null, id);
    if (req.status === 404) {
        return null;
    } else if (req.status !== 200) {
        throw Error(req.statusText);
    }
    return req.response;
}
Couch.prototype.write = function (doc) {
    var req = this.http("PUT", doc, doc._id);
    if (req.status !== 201) {
        throw Error(req.statusText);
    }
    doc._rev = req.response.rev;
}
Couch.prototype.remove = function (doc) {
    var req = this.http("DELETE", null, doc._id, {'rev':doc._rev});
    if (req.status !== 200) {
        throw Error(req.statusText);
    }
    doc._deleted = true;
    doc._rev = req.response.rev;
}


// helper needed under older JavaScript engines
Couch._keys = Object.keys || function (obj) {
    var keys = [], key;
    for (key in obj) if (obj.hasOwnProperty(key)) {
        keys.push(key);
    }
    return keys;
};

Couch.guessDB = function () {
    var x;
    if (location.protocol === "file:") {
        return "http://localhost:5984/dev";
    } else if ((x = location.href.indexOf("/_design")) !== -1) {
        return location.href.slice(0, x);
    } else {
        return "../..";
    }
}

Couch.REF_TYPE = "net.stemstorage.reference";

Couch.makeRef = function (doc, denormalize) {
    var reference = {};
    reference[Couch.REF_TYPE] = true;
    reference._id = doc._id;
    if (denormalize) denormalize.forEach(function (field) {
        reference[field] = doc[field];
    }), (reference._rev = doc._rev);
    return reference;
};
