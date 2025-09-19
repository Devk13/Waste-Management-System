"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WtnLink = void 0;
exports.findWtnUrl = findWtnUrl;
// path: frontend/src/components/WtnLink.tsx
var react_1 = require("react");
function joinUrl(base, path) {
    var b = base.endsWith("/") ? base.slice(0, -1) : base;
    var p = path.startsWith("/") ? path : "/".concat(path);
    return "".concat(b).concat(p);
}
var WtnLink = function (_a) {
    var baseUrl = _a.baseUrl, wtnPdfUrl = _a.wtnPdfUrl, className = _a.className;
    var htmlUrl = "".concat(joinUrl(baseUrl, wtnPdfUrl), "?format=html");
    var pdfUrl = "".concat(joinUrl(baseUrl, wtnPdfUrl), "?format=pdf");
    return (<div className={className !== null && className !== void 0 ? className : "flex items-center gap-2 mt-2"}>
      {/* why: let users preview quickly or grab a real PDF */}
      <a href={htmlUrl} target="_blank" rel="noreferrer" className="px-3 py-2 rounded-xl shadow hover:opacity-90 border border-slate-600">
        Open WTN (HTML)
      </a>
      <a href={pdfUrl} target="_blank" rel="noreferrer" className="px-3 py-2 rounded-xl shadow hover:opacity-90 border border-slate-600">
        Open PDF
      </a>
      <button onClick={function () { return navigator.clipboard.writeText(htmlUrl); }} className="px-3 py-2 rounded-xl shadow hover:opacity-90 border border-slate-600">
        Copy link
      </button>
    </div>);
};
exports.WtnLink = WtnLink;
// Helper to safely find wtn_pdf_url in any response object
function findWtnUrl(resp) {
    if (!resp || typeof resp !== "object")
        return null;
    var obj = resp;
    if (typeof obj.wtn_pdf_url === "string" && obj.wtn_pdf_url)
        return obj.wtn_pdf_url;
    // scan shallow arrays/objects (defensive)
    for (var _i = 0, _a = Object.values(obj); _i < _a.length; _i++) {
        var v = _a[_i];
        if (typeof v === "string" && v.includes("/wtn/") && v.endsWith(".pdf"))
            return v;
        if (v && typeof v === "object") {
            var nested = findWtnUrl(v);
            if (nested)
                return nested;
        }
    }
    return null;
}
