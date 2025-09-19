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
exports.ToastProvider = ToastProvider;
exports.useToast = useToast;
// path: frontend/src/components/Toast.tsx
var react_1 = require("react");
var Ctx = (0, react_1.createContext)(null);
var seq = 1;
function ToastProvider(_a) {
    var children = _a.children;
    var _b = (0, react_1.useState)([]), items = _b[0], setItems = _b[1];
    var push = (0, react_1.useCallback)(function (t) {
        setItems(function (prev) { return __spreadArray(__spreadArray([], prev, true), [t], false); });
        var ttl = 3500;
        setTimeout(function () { return setItems(function (prev) { return prev.filter(function (x) { return x.id !== t.id; }); }); }, ttl);
    }, []);
    var ctxVal = (0, react_1.useMemo)(function () { return ({ push: push }); }, [push]);
    return (<Ctx.Provider value={ctxVal}>
      {children}
      <div className="pointer-events-none fixed left-1/2 top-3 z-[1000] w-full max-w-sm -translate-x-1/2 space-y-2 px-2">
        {items.map(function (t) { return (<div key={t.id} className={"pointer-events-auto rounded-xl border bg-white px-3 py-2 text-sm shadow ".concat(t.type === 'success' ? 'border-emerald-300' : 'border-rose-300')}>
            <div className="flex items-start gap-2">
              <span className={"mt-0.5 h-2.5 w-2.5 rounded-full ".concat(t.type === 'success' ? 'bg-emerald-500' : t.type === 'error' ? 'bg-rose-500' : 'bg-slate-400')}></span>
              <div className="flex-1 text-slate-800">{t.message}</div>
              <button className="text-slate-400 hover:text-slate-600" onClick={function () { return setItems(function (prev) { return prev.filter(function (x) { return x.id !== t.id; }); }); }}>×</button>
            </div>
          </div>); })}
      </div>
    </Ctx.Provider>);
}
function useToast() {
    var ctx = (0, react_1.useContext)(Ctx);
    if (!ctx)
        return { success: function () { }, error: function () { }, info: function () { } };
    return {
        success: function (m) { return ctx.push({ id: seq++, type: 'success', message: m }); },
        error: function (m) { return ctx.push({ id: seq++, type: 'error', message: m }); },
        info: function (m) { return ctx.push({ id: seq++, type: 'info', message: m }); },
    };
}
