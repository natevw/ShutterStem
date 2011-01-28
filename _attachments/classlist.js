// https://developer.mozilla.org/en/DOM/element.classList
function ClassList(element) {
    this.element = element;
    this.list = {};
    element.className.split(" ").forEach(function (token) { this.list[token] = true; }, this);
}
ClassList.prototype._update = function () {
    this.element.className = Object.keys(this.list).join(" ");
};
ClassList.prototype.add = function (token) {
    this.list[token] = true;
    this._update();
};
ClassList.prototype.remove = function (token) {
    delete this.list[token];
    this._update();
};
ClassList.prototype.contains = function (token) {
    return (token in this.list);
};
ClassList.prototype.toggle = function (token) {
    var contained = this.contains(token);
    this[contained ? "remove" : "add"](token);
    return !contained;
};