"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = Toaster;
// frontend/src/ui/Toaster.tsx
var react_1 = require("react");
var toast_1 = require("./toast");
function Badge(_a) {
    var kind = _a.kind;
    return <span className={"badge ".concat(kind)}>{kind}</span>;
}
function Toaster() {
    var _a = react_1.default.useState([]), toasts = _a[0], setToasts = _a[1];
    react_1.default.useEffect(function () { return (0, toast_1.onToast)(setToasts); }, []);
    return (<div className="toaster">
      {toasts.map(function (t) {
            var _a;
            return (<div key={t.id} className={"toast ".concat(t.kind)} role="status" onClick={function () { return (0, toast_1.dismiss)(t.id); }}>
          <div className="row">
            <Badge kind={t.kind}/>
            <strong>{(_a = t.title) !== null && _a !== void 0 ? _a : (t.kind === "error" ? "Error" : "Notice")}</strong>
          </div>
          {t.msg ? <div className="muted">{t.msg}</div> : null}
        </div>);
        })}
    </div>);
}
