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
exports.default = WtnAdmin;
var react_1 = require("react");
function apiBase() {
    // Why: allow VITE_API_BASE override, else same-origin
    var env = import.meta.env;
    var base = env === null || env === void 0 ? void 0 : env.VITE_API_BASE;
    return base && base.length ? base.replace(/\/$/, "") : "";
}
function WtnAdmin() {
    var _this = this;
    var _a = react_1.default.useState(""), q = _a[0], setQ = _a[1];
    var _b = react_1.default.useState([]), items = _b[0], setItems = _b[1];
    var _c = react_1.default.useState(1), page = _c[0], setPage = _c[1];
    var pageSize = react_1.default.useState(20)[0];
    var _d = react_1.default.useState(0), total = _d[0], setTotal = _d[1];
    var _e = react_1.default.useState(false), loading = _e[0], setLoading = _e[1];
    var _f = react_1.default.useState(null), error = _f[0], setError = _f[1];
    var load = react_1.default.useCallback(function () {
        var args_1 = [];
        for (var _i = 0; _i < arguments.length; _i++) {
            args_1[_i] = arguments[_i];
        }
        return __awaiter(_this, __spreadArray([], args_1, true), void 0, function (p, query) {
            var url, res, data, e_1;
            if (p === void 0) { p = page; }
            if (query === void 0) { query = q; }
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        setLoading(true);
                        setError(null);
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 4, 5, 6]);
                        url = new URL("".concat(apiBase(), "/wtn"), window.location.origin);
                        if (query)
                            url.searchParams.set("q", query);
                        url.searchParams.set("page", String(p));
                        url.searchParams.set("page_size", String(pageSize));
                        return [4 /*yield*/, fetch(url.toString())];
                    case 2:
                        res = _a.sent();
                        if (!res.ok)
                            throw new Error("HTTP ".concat(res.status));
                        return [4 /*yield*/, res.json()];
                    case 3:
                        data = _a.sent();
                        setItems(data.items);
                        setPage(data.page);
                        setTotal(data.total);
                        return [3 /*break*/, 6];
                    case 4:
                        e_1 = _a.sent();
                        setError(e_1.message || String(e_1));
                        return [3 /*break*/, 6];
                    case 5:
                        setLoading(false);
                        return [7 /*endfinally*/];
                    case 6: return [2 /*return*/];
                }
            });
        });
    }, [page, q, pageSize]);
    react_1.default.useEffect(function () { load(1); /* first load */ }, []);
    var pages = Math.max(1, Math.ceil(total / pageSize));
    return (<div style={{ maxWidth: 1100, margin: "24px auto", padding: "0 12px" }}>
      <h1 style={{ fontSize: 22, marginBottom: 12 }}>Waste Transfer Notes</h1>

      <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "center" }}>
        <input placeholder="Search by ID or number…" value={q} onChange={function (e) { return setQ(e.target.value); }} onKeyDown={function (e) { return e.key === "Enter" && load(1, q); }} style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid #d1d5db", minWidth: 280 }}/>
        <button onClick={function () { return load(1, q); }} disabled={loading} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #111827", background: "#111827", color: "white" }}>
          Search
        </button>
        <button onClick={function () { setQ(""); load(1, ""); }} disabled={loading} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #e5e7eb", background: "white" }}>
          Clear
        </button>
        <div style={{ marginLeft: "auto", color: "#6b7280" }}>
          {loading ? "Loading…" : "Total: ".concat(total)}
        </div>
      </div>

      {error && (<div style={{ background: "#fee2e2", border: "1px solid #fecaca", color: "#991b1b", padding: 10, borderRadius: 8, marginBottom: 12 }}>
          {error}
        </div>)}

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", background: "#f9fafb" }}>
              <th style={{ padding: 10, borderBottom: "1px solid #e5e7eb" }}>WTN # / ID</th>
              <th style={{ padding: 10, borderBottom: "1px solid #e5e7eb" }}>Created</th>
              <th style={{ padding: 10, borderBottom: "1px solid #e5e7eb" }}>Quantity</th>
              <th style={{ padding: 10, borderBottom: "1px solid #e5e7eb" }}>Waste</th>
              <th style={{ padding: 10, borderBottom: "1px solid #e5e7eb" }}>Destination</th>
              <th style={{ padding: 10, borderBottom: "1px solid #e5e7eb" }}>Driver / Vehicle</th>
              <th style={{ padding: 10, borderBottom: "1px solid #e5e7eb" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && !loading && (<tr><td colSpan={7} style={{ padding: 16, color: "#6b7280" }}>No WTNs</td></tr>)}
            {items.map(function (it) {
            var label = it.number || it.id;
            var base = apiBase() || "";
            var pdf = "".concat(base, "/wtn/").concat(it.id, ".pdf");
            var html = "".concat(base, "/wtn/").concat(it.id, "/html");
            return (<tr key={it.id}>
                  <td style={{ padding: 10, borderBottom: "1px solid #f3f4f6" }}>
                    <div style={{ fontWeight: 600 }}>{label}</div>
                    <div style={{ fontSize: 12, color: "#6b7280" }}>{it.id}</div>
                  </td>
                  <td style={{ padding: 10, borderBottom: "1px solid #f3f4f6" }}>{it.created_at || "-"}</td>
                  <td style={{ padding: 10, borderBottom: "1px solid #f3f4f6" }}>{it.quantity || "-"}</td>
                  <td style={{ padding: 10, borderBottom: "1px solid #f3f4f6" }}>{it.waste_type || "-"}</td>
                  <td style={{ padding: 10, borderBottom: "1px solid #f3f4f6" }}>{it.destination || "-"}</td>
                  <td style={{ padding: 10, borderBottom: "1px solid #f3f4f6" }}>
                    {it.driver_name || "-"}
                    <div style={{ fontSize: 12, color: "#6b7280" }}>{it.vehicle_reg || ""}</div>
                  </td>
                  <td style={{ padding: 10, borderBottom: "1px solid #f3f4f6" }}>
                    <a href={pdf} target="_blank" rel="noreferrer" style={{ marginRight: 8 }}>PDF</a>
                    <a href={html} target="_blank" rel="noreferrer">HTML</a>
                  </td>
                </tr>);
        })}
          </tbody>
        </table>
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 12, alignItems: "center" }}>
        <button onClick={function () { return load(Math.max(1, page - 1)); }} disabled={loading || page <= 1} style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid #d1d5db", background: "white" }}>
          Prev
        </button>
        <span style={{ color: "#6b7280" }}>Page {page} / {pages}</span>
        <button onClick={function () { return load(Math.min(pages, page + 1)); }} disabled={loading || page >= pages} style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid #d1d5db", background: "white" }}>
          Next
        </button>
        <button onClick={function () { return load(page); }} disabled={loading} style={{ marginLeft: "auto", padding: "6px 10px", borderRadius: 8, border: "1px solid #111827", background: "#111827", color: "white" }}>
          Refresh
        </button>
      </div>
    </div>);
}
