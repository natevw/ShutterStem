var fermata;
(function () {
    var CONTENT = makeSet(['files', 'thumbnails', 'previews', 'files_put', 'chunked_upload', 'commit_chunked_upload']),
        NO_AUTO = makeSet(['account', 'delta', 'longpoll_delta', 'chunked_upload', 'fileops']);
    function makeSet(arr) {
        return arr.reduce(function (obj, k) { obj[k] = true; return obj; }, Object.create(null))
    }
    
    var plugin = function (transport, key) {
        this.base = "/1/";       // (placeholder)
        this.path = [];
        transport = transport.using('statusCheck').using('autoConvert', "application/json");
        
        return function (req, callback) {
            // TODO: this check is not production-grade, and there are a couple subdomains missing
            if (req.path[0] in CONTENT) req.base = "https://api-content.dropbox.com/1/";
            else req.base = "https://api.dropbox.com/1/";
            
            // HACK: allow elision of common "auto" path component
            if (req.path[0] in NO_AUTO || req.path[1] === 'auto') ;
            else req.path.splice(1, 0, 'auto');
            
            // via https://www.dropbox.com/developers/blog/45/using-oauth-20-with-the-core-api
            req.headers['Authorization'] = "Bearer "+key;
            
            return transport(req, callback);
        };
    };
    
    // some boilerplate to deal with browser vs. CommonJS
    if (fermata) {
        fermata.registerPlugin("couchdb", plugin);
    } else {
        module.exports = plugin;
    }
})();