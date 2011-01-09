function (doc) {
    // wildly varying SpiderMonkey versions FTL. aka: SpiderMonkey FTL.
    if (!Object.keys) {
        Object.keys = function (o) {
            var keys = [], key;
            for (key in o) if (o.hasOwnProperty(key)) {
                keys.push(key);
            }
            return keys;
        };
    }
    
    var IMAGE_TYPE = "testtype-image";
    if (!doc[IMAGE_TYPE]) return;
    
    Object.keys(doc.identifiers).forEach(function (name) {
        var identifier = doc.identifiers[name];
        if (name === "relative_path") {
            emit([identifier.source._id, identifier.path], name);
        } else {
            emit(identifier, name);
        }
    });
};
