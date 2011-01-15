function Couch(url) {
    this.url = url;
}
Couch.prototype.urlFor = function (path, query) {
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

var db = new Couch("http://localhost:5984/dev");

var loading = false;
var loadPending = false;
var lastImage = null;
function displayFetchedImages(viewResult) {
    viewResult.rows.forEach(function (row) {
        var img = new Image();
        img.className = "image";
        img.id = row.id;
        img.setAttribute('data-by_date-key', JSON.stringify(row.key));
        img.src = db.urlFor(row.id) + "/thumbnail/512.jpg";
        document.body.appendChild(img);
        lastImage = img;
    });
    loading = false;
    if (loadPending) {
        loadNextImages();
        loadPending = false;
    }
}
function loadNextImages() {
    if (loading) {
        loadPending = true;
        return;
    }
    
    var query = {reduce:false, limit:10};
    if (lastImage) {
        query.startkey = lastImage.getAttribute('data-by_date-key');
        query.startkey_docid = lastImage.id;
        query.skip = 1;
    }
    db.get("_design/shutterstem/_view/by_date", query, displayFetchedImages);
    loading = true;
}

document.addEventListener('DOMContentLoaded', function () {
    loadNextImages();
}, false);

document.addEventListener('scroll', function () {
    if ((window.pageYOffset + window.innerHeight) > (document.height - 50)) {
        loadNextImages();
    }
}, false);
