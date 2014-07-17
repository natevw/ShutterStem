function ShutterStemSelection() {
    var self = this;
    function updateSelection () {
        try {
            self._cachedSelection = JSON.parse(localStorage.shutterstem_selection);
        } catch (e) {
            self._cachedSelection = {};
        }
        ShutterStemSelection._triggerEvent();
    }
    
    window.addEventListener("storage", function (e) {
        if (e.storageArea === localStorage && e.key == 'shutterstem_selection') {
            updateSelection();
        }
    }, false);
    updateSelection();
}

ShutterStemSelection._triggerEvent = function () {
    var e = document.createEvent("Event");
    e.initEvent('shutterstem-selectionchange', false, false);
    window.dispatchEvent(e);
};

ShutterStemSelection.prototype.set = function (id, state) {
    if (!!this._cachedSelection[id] == !!state) return;
    
    if (state) {
        this._cachedSelection[id] = true;
    } else {
        delete this._cachedSelection[id];
    }
    localStorage.shutterstem_selection = JSON.stringify(this._cachedSelection);
    ShutterStemSelection._triggerEvent();
};

ShutterStemSelection.prototype.contains = function (id) {
    return !!this._cachedSelection[id];
};

ShutterStemSelection.prototype.toggle = function (id) {
    var newState = !this.contains(id);
    this.set(id, newState);
    return newState;
};

ShutterStemSelection.prototype.clear = function () {
    this._cachedSelection = {};
    localStorage.shutterstem_selection = JSON.stringify(this._cachedSelection);
    ShutterStemSelection._triggerEvent();
};

ShutterStemSelection.prototype.getArray = function (id) {
    return Object.keys(this._cachedSelection);
};
