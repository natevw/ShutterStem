/*
 flatstache.js - Logic-less, section-less templates in JavaScript. Expands simple (flat) Mustache templates.
 (c) 2011 Nathan Vander Wilt and Aaron McCall. MIT license.
*/
var Flatstache = (function(){
    var _re3 = /{{{\s*(\w+)\s*}}}/g,
        _re2 = /{{\s*(\w+)\s*}}/g,
        _re1 = /[&\"'<>\\]/g,  // "
        _escape_map = {"&": "&amp;", "\\": "&#92;", "\"": "&quot;", "'": "&#39;", "<": "&lt;", ">": "&gt;"},
        _escapeHTML = function(s) {
            return s.replace(_re1, function(c) { return _escape_map[c]; });
        },
        pub = {};
    pub.to_html = function (template, data) {
        return template
            .replace(_re3, function (m, key) { return data[key] || ""; })
            .replace(_re2, function (m, key) { return _escapeHTML(data[key] || ""); });
    };
    pub.elementify = function (templateId, data) {
        var tmpDiv = document.createElement('div');
        tmpDiv.innerHTML = pub.to_html(document.getElementById(templateId).innerText, data);
        return tmpDiv.firstElementChild;
    };
    return pub;
})();