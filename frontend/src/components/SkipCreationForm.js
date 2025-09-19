"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = SkipCreateForm;
// ===========================
// frontend/src/components/SkipCreateForm.tsx  (complete)
// ===========================
var react_1 = require("react");
var api_1 = require("../api");
function SkipCreateForm() {
    var _this = this;
    var _a = (0, react_1.useState)(null), meta = _a[0], setMeta = _a[1];
    var _b = (0, react_1.useState)("QR-NEW-001"), qr = _b[0], setQr = _b[1];
    var _c = (0, react_1.useState)(""), color = _c[0], setColor = _c[1];
    var _d = (0, react_1.useState)(""), size = _d[0], setSize = _d[1];
    var _e = (0, react_1.useState)(""), notes = _e[0], setNotes = _e[1];
    var _f = (0, react_1.useState)(false), busy = _f[0], setBusy = _f[1];
    var _g = (0, react_1.useState)(null), out = _g[0], setOut = _g[1];
    (0, react_1.useEffect)(function () { api_1.api.meta().then(setMeta).catch(function () { return setMeta(null); }); }, []);
    var colorOptions = (0, react_1.useMemo)(function () {
        var _a, _b;
        var colors = (_b = (_a = meta === null || meta === void 0 ? void 0 : meta.skip) === null || _a === void 0 ? void 0 : _a.colors) !== null && _b !== void 0 ? _b : {};
        return Object.entries(colors).map(function (_a) {
            var _b, _c, _d;
            var key = _a[0], val = _a[1];
            var label = (_d = (_c = (_b = val === null || val === void 0 ? void 0 : val.label) !== null && _b !== void 0 ? _b : val === null || val === void 0 ? void 0 : val.name) !== null && _c !== void 0 ? _c : val === null || val === void 0 ? void 0 : val.meaning) !== null && _d !== void 0 ? _d : key;
            return { value: key, label: "".concat(key, " \u2014 ").concat(label) };
        });
    }, [meta]);
    var groupedSizeOptions = (0, react_1.useMemo)(function () {
        var _a, _b;
        var sizes = (_b = (_a = meta === null || meta === void 0 ? void 0 : meta.skip) === null || _a === void 0 ? void 0 : _a.sizes) !== null && _b !== void 0 ? _b : {};
        return Object.entries(sizes).map(function (_a) {
            var group = _a[0], items = _a[1];
            return ({
                group: group,
                items: items.map(function (v) { return ({ value: v, label: v }); }),
            });
        });
    }, [meta]);
    var submit = function () { return __awaiter(_this, void 0, void 0, function () {
        var payload, res, e_1;
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    if (!qr || !color || !size) {
                        setOut({ error: "Missing required fields" });
                        return [2 /*return*/];
                    }
                    setBusy(true);
                    _b.label = 1;
                case 1:
                    _b.trys.push([1, 3, 4, 5]);
                    payload = { qr: qr, color: color, size: size, notes: notes || undefined };
                    return [4 /*yield*/, (0, api_1.adminCreateSkip)(payload)];
                case 2:
                    res = _b.sent();
                    setOut(res);
                    return [3 /*break*/, 5];
                case 3:
                    e_1 = _b.sent();
                    setOut({ error: e_1 === null || e_1 === void 0 ? void 0 : e_1.message, detail: (_a = e_1 === null || e_1 === void 0 ? void 0 : e_1.response) === null || _a === void 0 ? void 0 : _a.data });
                    return [3 /*break*/, 5];
                case 4:
                    setBusy(false);
                    return [7 /*endfinally*/];
                case 5: return [2 /*return*/];
            }
        });
    }); };
    return (<section className="card">
      <h2>Create/Seed Skip</h2>
      {!meta ? <p className="muted">Loading meta…</p> : null}
      <div className="grid3">
        <label>QR
          <input value={qr} onChange={function (e) { return setQr(e.target.value); }} placeholder="QR code"/>
        </label>
        <label>Color (with meaning)
          <select value={color} onChange={function (e) { return setColor(e.target.value); }}>
            <option value="">Select color</option>
            {colorOptions.map(function (o) { return (<option key={o.value} value={o.value}>{o.label}</option>); })}
          </select>
        </label>
        <label>Size
          <select value={size} onChange={function (e) { return setSize(e.target.value); }}>
            <option value="">Select size</option>
            {groupedSizeOptions.map(function (g) { return (<optgroup key={g.group} label={g.group}>
                {g.items.map(function (it) { return (<option key={"".concat(g.group, ":").concat(it.value)} value={it.value}>{it.label}</option>); })}
              </optgroup>); })}
          </select>
        </label>
      </div>
      <div className="grid2" style={{ marginTop: 8 }}>
        <label>Notes
          <input value={notes} onChange={function (e) { return setNotes(e.target.value); }} placeholder="optional"/>
        </label>
      </div>
      <div className="row" style={{ marginTop: 10 }}>
        <button disabled={busy || !meta} onClick={submit}>Create / Seed</button>
        <span className="muted">Uses color + size from <code>/meta/config</code>. Falls back to dev seeding if needed.</span>
      </div>

      <div style={{ marginTop: 12 }}>
        {out ? (<details open className="result">
            <summary><strong>Result</strong></summary>
            <pre>{(0, api_1.pretty)(out)}</pre>
          </details>) : null}
      </div>
    </section>);
}
