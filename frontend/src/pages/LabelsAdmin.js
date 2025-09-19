"use strict";
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var __rest = (this && this.__rest) || function (s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
        t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
        for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
            if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
                t[p[i]] = s[p[i]];
        }
    return t;
};
var _a;
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = LabelsAdmin;
// path: frontend/src/pages/LabelsAdmin.tsx
var react_1 = require("react");
var apiBase = ((_a = import.meta.env) === null || _a === void 0 ? void 0 : _a.VITE_API_URL) || "http://127.0.0.1:8000"; // dev default
function FieldLabel(_a) {
    var children = _a.children;
    return <label className="block text-sm font-medium text-slate-600 mb-1">{children}</label>;
}
function TextInput(props) {
    var label = props.label, rest = __rest(props, ["label"]);
    return (<div className="mb-4">
      {label && <FieldLabel>{label}</FieldLabel>}
      <input {...rest} className="w-full rounded-xl border px-3 py-2 outline-none focus:ring focus:ring-slate-300"/>
    </div>);
}
function LinkRow(_a) {
    var href = _a.href, label = _a.label;
    var fileName = (0, react_1.useMemo)(function () { return href.split("/").pop() || label; }, [href, label]);
    return (<div className="flex items-center justify-between rounded-xl border p-3">
      <span className="truncate text-sm">{fileName}</span>
      <div className="flex items-center gap-2">
        <a href={"".concat(apiBase).concat(href)} target="_blank" rel="noreferrer" className="rounded-lg border px-3 py-1 text-sm hover:bg-slate-50">
          Open
        </a>
        <a href={"".concat(apiBase).concat(href)} download className="rounded-lg bg-slate-900 px-3 py-1 text-sm text-white hover:bg-slate-800">
          Download
        </a>
      </div>
    </div>);
}
function LabelsAdmin() {
    var _a, _b, _c;
    var _d = (0, react_1.useState)({ owner_org_id: "" }), form = _d[0], setForm = _d[1];
    var _e = (0, react_1.useState)(false), loading = _e[0], setLoading = _e[1];
    var _f = (0, react_1.useState)(null), error = _f[0], setError = _f[1];
    var _g = (0, react_1.useState)(null), result = _g[0], setResult = _g[1];
    function handleCreate(e) {
        return __awaiter(this, void 0, void 0, function () {
            var r, msg, data, err_1;
            var _a;
            return __generator(this, function (_b) {
                switch (_b.label) {
                    case 0:
                        e.preventDefault();
                        setError(null);
                        setResult(null);
                        if (!form.owner_org_id) {
                            setError("Owner org ID is required");
                            return [2 /*return*/];
                        }
                        setLoading(true);
                        _b.label = 1;
                    case 1:
                        _b.trys.push([1, 6, 7, 8]);
                        return [4 /*yield*/, fetch("".concat(apiBase, "/skips"), {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    owner_org_id: form.owner_org_id,
                                    qr_code: form.qr_code || null,
                                    assigned_commodity_id: form.assigned_commodity_id || null,
                                    zone_id: form.zone_id || null,
                                }),
                            })];
                    case 2:
                        r = _b.sent();
                        if (!!r.ok) return [3 /*break*/, 4];
                        return [4 /*yield*/, r.text()];
                    case 3:
                        msg = _b.sent();
                        throw new Error("".concat(r.status, ": ").concat(msg || r.statusText));
                    case 4: return [4 /*yield*/, r.json()];
                    case 5:
                        data = (_b.sent());
                        setResult(data);
                        return [3 /*break*/, 8];
                    case 6:
                        err_1 = _b.sent();
                        setError((_a = err_1 === null || err_1 === void 0 ? void 0 : err_1.message) !== null && _a !== void 0 ? _a : "Request failed");
                        return [3 /*break*/, 8];
                    case 7:
                        setLoading(false);
                        return [7 /*endfinally*/];
                    case 8: return [2 /*return*/];
                }
            });
        });
    }
    return (<div className="mx-auto max-w-3xl p-4">
      <div className="mb-6 rounded-2xl border bg-white p-5 shadow-sm">
        <h2 className="mb-1 text-xl font-semibold">Create Labels</h2>
        <p className="mb-4 text-sm text-slate-600">
          POST <code className="rounded bg-slate-100 px-1 py-0.5">/skips</code> and get a PDF + 3 PNG label files.
        </p>

        <form onSubmit={handleCreate} className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <TextInput label="Owner Org ID (UUID)" placeholder="00000000-0000-0000-0000-000000000000" value={form.owner_org_id} onChange={function (e) { return setForm(__assign(__assign({}, form), { owner_org_id: e.target.value })); }} required/>
          </div>

          <TextInput label="Custom QR Code (optional)" placeholder="SK-ABC123" value={(_a = form.qr_code) !== null && _a !== void 0 ? _a : ""} onChange={function (e) { return setForm(__assign(__assign({}, form), { qr_code: e.target.value })); }}/>

          <TextInput label="Assigned Commodity ID (optional)" placeholder="uuid" value={(_b = form.assigned_commodity_id) !== null && _b !== void 0 ? _b : ""} onChange={function (e) { return setForm(__assign(__assign({}, form), { assigned_commodity_id: e.target.value })); }}/>

          <TextInput label="Zone ID (optional)" placeholder="uuid" value={(_c = form.zone_id) !== null && _c !== void 0 ? _c : ""} onChange={function (e) { return setForm(__assign(__assign({}, form), { zone_id: e.target.value })); }}/>

          <div className="md:col-span-2 mt-2 flex items-center gap-3">
            <button type="submit" disabled={loading} className="rounded-xl bg-slate-900 px-4 py-2 text-white shadow-sm hover:bg-slate-800 disabled:opacity-50">
              {loading ? "Creating…" : "Create Labels"}
            </button>
            <button type="button" className="rounded-xl border px-4 py-2 hover:bg-slate-50" onClick={function () {
            setForm({ owner_org_id: "" });
            setError(null);
            setResult(null);
        }}>
              Reset
            </button>
          </div>
        </form>

        {error && (<div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>)}
      </div>

      {result && (<div className="rounded-2xl border bg-white p-5 shadow-sm">
          <h3 className="mb-3 text-lg font-semibold">Assets generated</h3>

          <div className="mb-4 grid gap-3">
            <LinkRow href={result.labels_pdf_url} label="labels.pdf"/>
            {result.label_png_urls.map(function (u, i) { return (<LinkRow key={u} href={u} label={"labels/".concat(i + 1, ".png")}/>); })}
          </div>

          <div className="text-sm text-slate-600">
            <div className="mb-1">Skip ID: {result.id}</div>
            <div className="mb-1">QR Code: {result.qr_code}</div>
            <div>Owner Org: {result.owner_org_id}</div>
          </div>
        </div>)}
    </div>);
}
