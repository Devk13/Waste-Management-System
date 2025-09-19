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
exports.default = ActionCard;
// path: frontend/src/components/ActionCard.tsx
var react_1 = require("react");
var lucide_react_1 = require("lucide-react");
var api_1 = require("../api");
var SearchSelect_1 = require("./SearchSelect");
var Toast_1 = require("./Toast");
var _a = (0, react_1.useState)(null), msg = _a[0], setMsg = _a[1];
var _b = (0, react_1.useState)(null), busy = _b[0], setBusy = _b[1];
var _c = (0, react_1.useState)(undefined), toZone = _c[0], setToZone = _c[1];
var _d = (0, react_1.useState)(undefined), fromZone = _d[0], setFromZone = _d[1];
var _e = (0, react_1.useState)(undefined), facility = _e[0], setFacility = _e[1];
function ActionCard(_a) {
    var _this = this;
    var qr = _a.qr, zoneId = _a.zoneId;
    var _b = (0, react_1.useState)(null), busy = _b[0], setBusy = _b[1];
    var _c = (0, react_1.useState)(null), msg = _c[0], setMsg = _c[1];
    var toast = (0, Toast_1.useToast)();
    // Pickers
    var _d = (0, react_1.useState)(null), toZone = _d[0], setToZone = _d[1];
    var _e = (0, react_1.useState)(zoneId ? { id: zoneId, label: zoneId } : null), fromZone = _e[0], setFromZone = _e[1];
    var _f = (0, react_1.useState)(null), facility = _f[0], setFacility = _f[1];
    // Numeric inputs
    var _g = (0, react_1.useState)(''), gross = _g[0], setGross = _g[1];
    var _h = (0, react_1.useState)(''), tare = _h[0], setTare = _h[1];
    var _j = (0, react_1.useState)(''), ticket = _j[0], setTicket = _j[1];
    // Remember last used selections
    (0, react_1.useEffect)(function () {
        try {
            var z = JSON.parse(localStorage.getItem('last:zone') || 'null');
            if (z)
                setToZone(z);
        }
        catch (_a) { }
        try {
            var f = JSON.parse(localStorage.getItem('last:facility') || 'null');
            if (f)
                setFacility(f);
        }
        catch (_b) { }
    }, []);
    // remember last selection
    function saveLast(key, opt) {
        if (!opt)
            return;
        try {
            localStorage.setItem("last:".concat(key), JSON.stringify(opt));
        }
        catch (_a) { }
    }
    // Data loaders for SearchSelect
    var loadZones = function (q) { return __awaiter(_this, void 0, void 0, function () { return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, (0, api_1.searchZones)(q)];
            case 1: return [2 /*return*/, (_a.sent()).map(function (z) { return ({ id: z.id, label: z.name, sublabel: z.site_name }); })];
        }
    }); }); };
    var loadFacilities = function (q) { return __awaiter(_this, void 0, void 0, function () { return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, (0, api_1.searchFacilities)(q)];
            case 1: return [2 /*return*/, (_a.sent()).map(function (f) { return ({ id: f.id, label: f.name, sublabel: f.org_name }); })];
        }
    }); }); };
    function run(name, fn) {
        return __awaiter(this, void 0, void 0, function () {
            var e_1, m;
            var _a, _b, _c, _d;
            return __generator(this, function (_e) {
                switch (_e.label) {
                    case 0:
                        _e.trys.push([0, 2, 3, 4]);
                        setBusy(name);
                        setMsg(null);
                        return [4 /*yield*/, fn()];
                    case 1:
                        _e.sent();
                        toast.success('OK');
                        return [3 /*break*/, 4];
                    case 2:
                        e_1 = _e.sent();
                        m = (_d = (_c = (_b = (_a = e_1 === null || e_1 === void 0 ? void 0 : e_1.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.detail) !== null && _c !== void 0 ? _c : e_1 === null || e_1 === void 0 ? void 0 : e_1.message) !== null && _d !== void 0 ? _d : 'Error';
                        setMsg(String(m));
                        toast.error(String(m));
                        throw e_1;
                    case 3:
                        setBusy(null);
                        return [7 /*endfinally*/];
                    case 4: return [2 /*return*/];
                }
            });
        });
    }
    var numberOrEmpty = function (v) {
        if (v.trim() === '')
            return '';
        var n = Number(v);
        return Number.isNaN(n) ? '' : n;
    };
    return (<div className="grid gap-4">
      {msg && (<div className="text-sm text-center text-slate-700 bg-slate-100 rounded p-2">{msg}</div>)}

      {/* Deliver Empty */}
      <div className="p-4 rounded-2xl border bg-white shadow-sm">
        <div className="flex items-center gap-2 mb-2"><lucide_react_1.Package2 /> <b>Deliver Empty</b></div>
        <div className="grid gap-2 sm:grid-cols-2">
          <SearchSelect_1.default placeholder="Destination zone" value={toZone} onChange={setToZone} loadOptions={loadZones} allowClear/>
          <button className="btn" disabled={!toZone || !!busy} onClick={function () {
            return run('Delivered', function () { return __awaiter(_this, void 0, void 0, function () { return __generator(this, function (_a) {
                return [2 /*return*/, (0, api_1.deliverEmpty)(qr, toZone.id)];
            }); }); });
        }}>
            Deliver
          </button>
        </div>
      </div>

      {/* Collect Full */}
      <div className="p-4 rounded-2xl border bg-white shadow-sm">
        <div className="flex items-center gap-2 mb-2"><lucide_react_1.Truck /> <b>Collect Full</b></div>
        <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
          <SearchSelect_1.default placeholder="From zone (optional)" value={fromZone} onChange={setFromZone} loadOptions={loadZones} allowClear/>
          <button className="btn" disabled={!!busy} onClick={function () {
            return run('Collected', function () { return __awaiter(_this, void 0, void 0, function () {
                var _a, _b;
                return __generator(this, function (_c) {
                    switch (_c.label) {
                        case 0: return [4 /*yield*/, (0, api_1.collectFull)({
                                qr_code: qr,
                                from_zone_id: (_a = fromZone === null || fromZone === void 0 ? void 0 : fromZone.id) !== null && _a !== void 0 ? _a : undefined, // <- was ?? null
                                destination_facility_id: (_b = facility === null || facility === void 0 ? void 0 : facility.id) !== null && _b !== void 0 ? _b : undefined // <- was ?? null
                            })];
                        case 1:
                            _c.sent();
                            return [2 /*return*/];
                    }
                });
            }); });
        }}>
            Collect
          </button>
        </div>
      </div>

      {/* Drop at Facility */}
      <div className="p-4 rounded-2xl border bg-white shadow-sm">
        <div className="flex items-center gap-2 mb-2"><lucide_react_1.Factory /> <b>Drop at Facility</b></div>
        <div className="grid gap-2 sm:grid-cols-4 items-start">
          <SearchSelect_1.default placeholder="Facility" value={facility} onChange={function (v) { setFacility(v); if (v)
        saveLast('facility', v); }} loadOptions={loadFacilities}/>
          <input className="input" placeholder="Gross kg" inputMode="numeric" value={gross} onChange={function (e) { return setGross(numberOrEmpty(e.target.value)); }}/>
          <input className="input" placeholder="Tare kg" inputMode="numeric" value={tare} onChange={function (e) { return setTare(numberOrEmpty(e.target.value)); }}/>
          <div className="flex justify-end">
            <button className="btn" disabled={!facility || !!busy} onClick={function () {
            return run('Dropped', function () { return __awaiter(_this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, (0, api_1.dropAtFacility)({
                            qr_code: qr,
                            facility_id: facility.id,
                            gross_kg: gross === '' ? undefined : Number(gross),
                            tare_kg: tare === '' ? undefined : Number(tare),
                            ticket_no: ticket || undefined,
                        })];
                });
            }); });
        }}>
              Submit
            </button>
          </div>
        </div>
        <div className="grid gap-2 sm:grid-cols-2 mt-2">
          <input className="input" placeholder="Weigh Ticket # (optional)" value={ticket} onChange={function (e) { return setTicket(e.target.value); }}/>
        </div>
      </div>

      {/* Return Empty */}
      <div className="p-4 rounded-2xl border bg-white shadow-sm">
        <div className="flex items-center gap-2 mb-2"><lucide_react_1.ArrowLeftRight /> <b>Return Empty</b></div>
        <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
          <SearchSelect_1.default placeholder="Select destination zone" value={toZone} onChange={function (v) { setToZone(v); if (v)
        saveLast('zone', v); }} loadOptions={loadZones}/>
          <button className="btn" disabled={!toZone || !!busy} onClick={function () {
            return run('Returned', function () { return __awaiter(_this, void 0, void 0, function () { return __generator(this, function (_a) {
                return [2 /*return*/, (0, api_1.returnEmpty)(qr, toZone.id)];
            }); }); });
        }}>
            Return
          </button>
        </div>
      </div>
    </div>);
}
