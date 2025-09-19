"use strict";
var __spreadArray = (this && this.__spreadArray) || function (to, from, pack) {
    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
            if (!ar) ar = Array.prototype.slice.call(from, 0, i);
            ar[i] = from[i];
        }
    }
    return to.concat(ar || Array.prototype.slice.call(from));
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.toast = void 0;
exports.dismiss = dismiss;
exports.onToast = onToast;
var listeners = new Set();
var queue = [];
function emit() { for (var _i = 0, listeners_1 = listeners; _i < listeners_1.length; _i++) {
    var l = listeners_1[_i];
    l(queue);
} }
function id() { return Math.random().toString(36).slice(2); }
function push(t) {
    var _a;
    queue = __spreadArray([t], queue, true).slice(0, 5);
    emit();
    var ttl = (_a = t.ms) !== null && _a !== void 0 ? _a : (t.kind === "error" ? 6000 : 3000);
    setTimeout(function () { return dismiss(t.id); }, ttl);
}
function dismiss(tid) { queue = queue.filter(function (x) { return x.id !== tid; }); emit(); }
/** Subscribe; returns unsubscribe (void cleanup). */
function onToast(cb) {
    listeners.add(cb);
    cb(queue);
    return function () { listeners.delete(cb); }; // <- ensure void
}
exports.toast = {
    info: function (msg, title, ms) { return push({ id: id(), kind: "info", title: title, msg: msg, ms: ms }); },
    success: function (msg, title, ms) { return push({ id: id(), kind: "success", title: title, msg: msg, ms: ms }); },
    error: function (msg, title, ms) { return push({ id: id(), kind: "error", title: title, msg: msg, ms: ms }); },
};
