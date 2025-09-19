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
exports.default = App;
// ======================================================================
// path: frontend/src/App.tsx
// ======================================================================
var react_1 = require("react");
var api_1 = require("./api");
require("./styles.css");
var Toaster_1 = require("./ui/Toaster");
var toast_1 = require("./ui/toast");
var SkipCreationForm_1 = require("./components/SkipCreationForm");
function safeNum(v) { var n = Number(v); return Number.isFinite(n) ? n : 0; }
function driverLabel(d) { var _a, _b, _c, _d; return (_d = (_c = (_b = (_a = d === null || d === void 0 ? void 0 : d.full_name) !== null && _a !== void 0 ? _a : d === null || d === void 0 ? void 0 : d.name) !== null && _b !== void 0 ? _b : d === null || d === void 0 ? void 0 : d.email) !== null && _c !== void 0 ? _c : d === null || d === void 0 ? void 0 : d.phone) !== null && _d !== void 0 ? _d : "(unnamed)"; }
function vehicleLabel(v) { var _a, _b, _c; return (_c = (_b = (_a = v === null || v === void 0 ? void 0 : v.reg_no) !== null && _a !== void 0 ? _a : v === null || v === void 0 ? void 0 : v.plate) !== null && _b !== void 0 ? _b : v === null || v === void 0 ? void 0 : v.id) !== null && _c !== void 0 ? _c : "(no reg)"; }
function findWtnUrl(resp) {
    if (!resp || typeof resp !== "object")
        return null;
    var obj = resp;
    if (typeof obj.wtn_pdf_url === "string" && obj.wtn_pdf_url)
        return obj.wtn_pdf_url;
    for (var _i = 0, _a = Object.values(obj); _i < _a.length; _i++) {
        var v = _a[_i];
        if (typeof v === "string" && v.includes("/wtn/") && v.endsWith(".pdf"))
            return v;
    }
    return null;
}
function joinUrl(base, path) {
    var b = base.endsWith("/") ? base.slice(0, -1) : base;
    var p = path.startsWith("/") ? path : "/".concat(path);
    return "".concat(b).concat(p);
}
function App() {
    var _this = this;
    var _a, _b, _c, _d, _e, _f, _g, _h, _j, _k, _l, _m;
    var _o = (0, react_1.useState)((0, api_1.getConfig)()), cfg = _o[0], setCfg = _o[1];
    var _p = (0, react_1.useState)(false), busy = _p[0], setBusy = _p[1];
    var _q = (0, react_1.useState)([]), out = _q[0], setOut = _q[1];
    var _r = (0, react_1.useState)(null), ver = _r[0], setVer = _r[1];
    // masters
    var _s = (0, react_1.useState)([]), drivers = _s[0], setDrivers = _s[1];
    var _t = (0, react_1.useState)([]), vehicles = _t[0], setVehicles = _t[1];
    var _u = (0, react_1.useState)(""), driverId = _u[0], setDriverId = _u[1];
    var _v = (0, react_1.useState)(""), vehId = _v[0], setVehId = _v[1];
    // driver flow inputs
    var _w = (0, react_1.useState)("QR123"), qr = _w[0], setQr = _w[1];
    var _x = (0, react_1.useState)("Alex"), driverName = _x[0], setDriverName = _x[1];
    var _y = (0, react_1.useState)("TEST-001"), vehReg = _y[0], setVehReg = _y[1];
    var _z = (0, react_1.useState)("ZONE_A"), zoneA = _z[0], setZoneA = _z[1];
    var _0 = (0, react_1.useState)("ZONE_B"), zoneB = _0[0], setZoneB = _0[1];
    var _1 = (0, react_1.useState)("ZONE_C"), zoneC = _1[0], setZoneC = _1[1];
    var _2 = (0, react_1.useState)(2500), gross = _2[0], setGross = _2[1];
    var _3 = (0, react_1.useState)(1500), tare = _3[0], setTare = _3[1];
    var _4 = (0, react_1.useState)("RECYCLING"), destType = _4[0], setDestType = _4[1];
    var _5 = (0, react_1.useState)("ECO MRF"), destName = _5[0], setDestName = _5[1];
    var _6 = (0, react_1.useState)("SITE1"), siteId = _6[0], setSiteId = _6[1];
    var pushOut = function (title, payload) {
        return setOut(function (xs) { return __spreadArray([{ title: title, payload: payload, at: new Date().toLocaleTimeString() }], xs, true).slice(0, 30); });
    };
    var save = function () { (0, api_1.setConfig)(cfg); setCfg((0, api_1.getConfig)()); pushOut("Saved config", cfg); toast_1.toast.success("Configuration saved"); };
    // load masters
    (0, react_1.useEffect)(function () {
        (function () { return __awaiter(_this, void 0, void 0, function () {
            var _a, e_1, _b, e_2;
            return __generator(this, function (_c) {
                switch (_c.label) {
                    case 0:
                        _c.trys.push([0, 2, , 3]);
                        _a = setDrivers;
                        return [4 /*yield*/, api_1.api.listDrivers()];
                    case 1:
                        _a.apply(void 0, [_c.sent()]);
                        return [3 /*break*/, 3];
                    case 2:
                        e_1 = _c.sent();
                        toast_1.toast.error("Failed to load drivers", e_1 === null || e_1 === void 0 ? void 0 : e_1.message);
                        return [3 /*break*/, 3];
                    case 3:
                        _c.trys.push([3, 5, , 6]);
                        _b = setVehicles;
                        return [4 /*yield*/, api_1.api.listVehicles()];
                    case 4:
                        _b.apply(void 0, [_c.sent()]);
                        return [3 /*break*/, 6];
                    case 5:
                        e_2 = _c.sent();
                        toast_1.toast.error("Failed to load vehicles", e_2 === null || e_2 === void 0 ? void 0 : e_2.message);
                        return [3 /*break*/, 6];
                    case 6: return [2 /*return*/];
                }
            });
        }); })();
    }, [cfg.base, cfg.adminKey]);
    // reflect selections into text fields
    (0, react_1.useEffect)(function () { var d = drivers.find(function (x) { return x.id === driverId; }); if (d)
        setDriverName(driverLabel(d)); }, [driverId, drivers]);
    (0, react_1.useEffect)(function () { var v = vehicles.find(function (x) { return x.id === vehId; }); if (v)
        setVehReg(vehicleLabel(v)); }, [vehId, vehicles]);
    var run = function (label, fn) { return __awaiter(_this, void 0, void 0, function () {
        var data, e_3, ae;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    setBusy(true);
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 3, 4, 5]);
                    return [4 /*yield*/, fn()];
                case 2:
                    data = _a.sent();
                    pushOut(label, data);
                    toast_1.toast.success("".concat(label, " \u2713"));
                    return [2 /*return*/, data];
                case 3:
                    e_3 = _a.sent();
                    ae = e_3 instanceof api_1.ApiError ? e_3 : null;
                    pushOut("".concat(label, " (ERR)"), { error: (ae === null || ae === void 0 ? void 0 : ae.message) || (e_3 === null || e_3 === void 0 ? void 0 : e_3.message) || String(e_3), code: ae === null || ae === void 0 ? void 0 : ae.code, fields: ae === null || ae === void 0 ? void 0 : ae.fields });
                    toast_1.toast.error((ae === null || ae === void 0 ? void 0 : ae.message) || (e_3 === null || e_3 === void 0 ? void 0 : e_3.message) || "Request failed", label);
                    throw e_3;
                case 4:
                    setBusy(false);
                    return [7 /*endfinally*/];
                case 5: return [2 /*return*/];
            }
        });
    }); };
    // mini creates
    var seedDriver = function () { return __awaiter(_this, void 0, void 0, function () {
        var name, r, _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    name = prompt("Driver full name", "Alex");
                    if (!name)
                        return [2 /*return*/];
                    return [4 /*yield*/, run("Create driver", function () { return api_1.api.createDriver({ name: name }); })];
                case 1:
                    r = _b.sent();
                    _a = setDrivers;
                    return [4 /*yield*/, api_1.api.listDrivers()];
                case 2:
                    _a.apply(void 0, [_b.sent()]);
                    setDriverId(r.id);
                    return [2 /*return*/];
            }
        });
    }); };
    var seedVehicle = function () { return __awaiter(_this, void 0, void 0, function () {
        var reg, r, _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    reg = prompt("Vehicle reg", "TEST-001");
                    if (!reg)
                        return [2 /*return*/];
                    return [4 /*yield*/, run("Create vehicle", function () { return api_1.api.createVehicle({ reg_no: reg }); })];
                case 1:
                    r = _b.sent();
                    _a = setVehicles;
                    return [4 /*yield*/, api_1.api.listVehicles()];
                case 2:
                    _a.apply(void 0, [_b.sent()]);
                    setVehId(r.id);
                    return [2 /*return*/];
            }
        });
    }); };
    // Admin inline edit state
    var selDriver = (0, react_1.useMemo)(function () { var _a; return (_a = drivers.find(function (d) { return d.id === driverId; })) !== null && _a !== void 0 ? _a : null; }, [drivers, driverId]);
    var selVehicle = (0, react_1.useMemo)(function () { var _a; return (_a = vehicles.find(function (v) { return v.id === vehId; })) !== null && _a !== void 0 ? _a : null; }, [vehicles, vehId]);
    var _7 = (0, react_1.useState)(null), drvEdit = _7[0], setDrvEdit = _7[1];
    var _8 = (0, react_1.useState)(null), vehEdit = _8[0], setVehEdit = _8[1];
    var _9 = (0, react_1.useState)({}), drvErrs = _9[0], setDrvErrs = _9[1];
    var _10 = (0, react_1.useState)({}), vehErrs = _10[0], setVehErrs = _10[1];
    (0, react_1.useEffect)(function () {
        var _a, _b, _c, _d, _e;
        if (selDriver)
            setDrvEdit({
                name: (_b = (_a = selDriver.full_name) !== null && _a !== void 0 ? _a : selDriver.name) !== null && _b !== void 0 ? _b : "",
                phone: (_c = selDriver.phone) !== null && _c !== void 0 ? _c : "",
                license_no: (_d = selDriver.license_no) !== null && _d !== void 0 ? _d : "",
                active: Boolean((_e = selDriver.active) !== null && _e !== void 0 ? _e : true),
            });
        else
            setDrvEdit(null);
        setDrvErrs({});
    }, [selDriver]);
    (0, react_1.useEffect)(function () {
        var _a, _b, _c, _d;
        if (selVehicle)
            setVehEdit({
                reg_no: (_a = selVehicle.reg_no) !== null && _a !== void 0 ? _a : "",
                make: (_b = selVehicle.make) !== null && _b !== void 0 ? _b : "",
                model: (_c = selVehicle.model) !== null && _c !== void 0 ? _c : "",
                active: Boolean((_d = selVehicle.active) !== null && _d !== void 0 ? _d : true),
            });
        else
            setVehEdit(null);
        setVehErrs({});
    }, [selVehicle]);
    // simple validators
    function validateDriver(p) {
        var _a;
        var e = {};
        if (!((_a = p.name) === null || _a === void 0 ? void 0 : _a.trim()))
            e.name = "Name is required";
        if (p.name && p.name.length > 80)
            e.name = "Name too long";
        return e;
    }
    function validateVehicle(p) {
        var _a;
        var e = {};
        if (!((_a = p.reg_no) === null || _a === void 0 ? void 0 : _a.trim()))
            e.reg_no = "Registration required";
        if (p.reg_no && p.reg_no.length > 32)
            e.reg_no = "Too long";
        return e;
    }
    var saveDriver = function () { return __awaiter(_this, void 0, void 0, function () {
        var errs, _a, e_4;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    if (!driverId || !drvEdit)
                        return [2 /*return*/];
                    errs = validateDriver(drvEdit);
                    setDrvErrs(errs);
                    if (Object.keys(errs).length) {
                        toast_1.toast.error("Fix validation errors", "Driver");
                        return [2 /*return*/];
                    }
                    _b.label = 1;
                case 1:
                    _b.trys.push([1, 4, , 5]);
                    return [4 /*yield*/, run("Update driver", function () { return api_1.api.updateDriver(driverId, drvEdit); })];
                case 2:
                    _b.sent();
                    _a = setDrivers;
                    return [4 /*yield*/, api_1.api.listDrivers()];
                case 3:
                    _a.apply(void 0, [_b.sent()]);
                    return [3 /*break*/, 5];
                case 4:
                    e_4 = _b.sent();
                    if (e_4 instanceof api_1.ApiError && e_4.fields)
                        setDrvErrs(function (prev) { return (__assign(__assign({}, prev), e_4.fields)); });
                    return [3 /*break*/, 5];
                case 5: return [2 /*return*/];
            }
        });
    }); };
    var deleteDriver = function () { return __awaiter(_this, void 0, void 0, function () {
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    if (!driverId)
                        return [2 /*return*/];
                    if (!confirm("Delete this driver?"))
                        return [2 /*return*/];
                    return [4 /*yield*/, run("Delete driver", function () { return api_1.api.deleteDriver(driverId); })];
                case 1:
                    _b.sent();
                    setDriverId("");
                    _a = setDrivers;
                    return [4 /*yield*/, api_1.api.listDrivers()];
                case 2:
                    _a.apply(void 0, [_b.sent()]);
                    return [2 /*return*/];
            }
        });
    }); };
    var saveVehicle = function () { return __awaiter(_this, void 0, void 0, function () {
        var errs, _a, e_5;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    if (!vehId || !vehEdit)
                        return [2 /*return*/];
                    errs = validateVehicle(vehEdit);
                    setVehErrs(errs);
                    if (Object.keys(errs).length) {
                        toast_1.toast.error("Fix validation errors", "Vehicle");
                        return [2 /*return*/];
                    }
                    _b.label = 1;
                case 1:
                    _b.trys.push([1, 4, , 5]);
                    return [4 /*yield*/, run("Update vehicle", function () { return api_1.api.updateVehicle(vehId, vehEdit); })];
                case 2:
                    _b.sent();
                    _a = setVehicles;
                    return [4 /*yield*/, api_1.api.listVehicles()];
                case 3:
                    _a.apply(void 0, [_b.sent()]);
                    return [3 /*break*/, 5];
                case 4:
                    e_5 = _b.sent();
                    if (e_5 instanceof api_1.ApiError && e_5.fields)
                        setVehErrs(function (prev) { return (__assign(__assign({}, prev), e_5.fields)); });
                    return [3 /*break*/, 5];
                case 5: return [2 /*return*/];
            }
        });
    }); };
    var deleteVehicle = function () { return __awaiter(_this, void 0, void 0, function () {
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    if (!vehId)
                        return [2 /*return*/];
                    if (!confirm("Delete this vehicle?"))
                        return [2 /*return*/];
                    return [4 /*yield*/, run("Delete vehicle", function () { return api_1.api.deleteVehicle(vehId); })];
                case 1:
                    _b.sent();
                    setVehId("");
                    _a = setVehicles;
                    return [4 /*yield*/, api_1.api.listVehicles()];
                case 2:
                    _a.apply(void 0, [_b.sent()]);
                    return [2 /*return*/];
            }
        });
    }); };
    var runAll = function () { return __awaiter(_this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, run("DEV ensure-skip", function () { return api_1.api.ensureSkipDev(qr); })];
                case 1:
                    _a.sent();
                    return [4 /*yield*/, run("driver/scan", function () { return api_1.api.scan(qr); })];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, run("driver/deliver-empty", function () { return api_1.api.deliverEmpty({ skip_qr: qr, to_zone_id: zoneC, driver_name: driverName, vehicle_reg: vehReg }); })];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, run("driver/relocate-empty", function () { return api_1.api.relocateEmpty({ skip_qr: qr, from_zone_id: zoneA, to_zone_id: zoneB, driver_name: driverName }); })];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, run("driver/collect-full", function () { return api_1.api.collectFull({
                            skip_qr: qr, destination_type: destType, destination_name: destName,
                            weight_source: "WEIGHBRIDGE", gross_kg: gross, tare_kg: tare, driver_name: driverName, site_id: siteId, vehicle_reg: vehReg
                        }); })];
                case 5:
                    _a.sent();
                    return [4 /*yield*/, run("driver/return-empty", function () { return api_1.api.returnEmpty({ skip_qr: qr, to_zone_id: zoneC, driver_name: driverName }); })];
                case 6:
                    _a.sent();
                    return [2 /*return*/];
            }
        });
    }); };
    // Versions badge
    var fetchVersions = function () { return __awaiter(_this, void 0, void 0, function () { var data; return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, run("meta/versions", api_1.api.versions)];
            case 1:
                data = _a.sent();
                setVer(data);
                return [2 /*return*/];
        }
    }); }); };
    var envText = (_b = (_a = ver === null || ver === void 0 ? void 0 : ver.backend) === null || _a === void 0 ? void 0 : _a.env) !== null && _b !== void 0 ? _b : "";
    var shaText = (_d = (_c = ver === null || ver === void 0 ? void 0 : ver.backend) === null || _c === void 0 ? void 0 : _c.sha) !== null && _d !== void 0 ? _d : "";
    var builtAt = (_f = (_e = ver === null || ver === void 0 ? void 0 : ver.backend) === null || _e === void 0 ? void 0 : _e.built_at) !== null && _f !== void 0 ? _f : "";
    return (<div className="wrap">
      <Toaster_1.default />
      <div className="header">
        <div>
          <h1>WMIS Dev Console</h1>
          <p className="muted">Driver flow + admin masters + WTN</p>
        </div>
        <div className="row">
          <div className="tag">{busy ? "running…" : "idle"}</div>
          {envText || shaText ? (<div className="tag" title={builtAt ? "built ".concat(builtAt) : undefined}>
              {envText ? envText : "env"} • {shaText || "sha"}
            </div>) : null}
        </div>
      </div>

      <section className="card">
        <h2>Config</h2>
        <div className="grid3">
          <label>Base URL<input value={cfg.base} onChange={function (e) { return setCfg(__assign(__assign({}, cfg), { base: e.target.value })); }}/></label>
          <label>Driver API Key<input value={(_g = cfg.apiKey) !== null && _g !== void 0 ? _g : ""} onChange={function (e) { return setCfg(__assign(__assign({}, cfg), { apiKey: e.target.value })); }}/></label>
          <label>Admin Key<input value={(_h = cfg.adminKey) !== null && _h !== void 0 ? _h : ""} onChange={function (e) { return setCfg(__assign(__assign({}, cfg), { adminKey: e.target.value })); }}/></label>
        </div>
        <div className="row"><button onClick={save}>Save</button></div>
      </section>

      <section className="card">
        <h2>Debug</h2>
        <div className="row">
          <button disabled={busy} onClick={function () { return run("_meta/ping", api_1.api.health); }}>Ping DB</button>
          <button disabled={busy} onClick={function () { return run("__debug/routes", api_1.api.routes); }}>Routes</button>
          <button disabled={busy} onClick={function () { return run("__debug/mounts", api_1.api.mounts); }}>Mounts</button>
          <button disabled={busy} onClick={function () { return run("skips/__smoke", api_1.api.skipsSmoke); }}>Skips Smoke</button>
          <button disabled={busy} onClick={fetchVersions}>Versions</button>
          <button disabled={busy} onClick={function () { return __awaiter(_this, void 0, void 0, function () {
            var r, u, href;
            var _a, _b;
            return __generator(this, function (_c) {
                switch (_c.label) {
                    case 0: return [4 /*yield*/, run("__debug/wtns", function () { return api_1.api.latestWtns(1); })];
                    case 1:
                        r = _c.sent();
                        u = (_b = (_a = r === null || r === void 0 ? void 0 : r.items) === null || _a === void 0 ? void 0 : _a[0]) === null || _b === void 0 ? void 0 : _b.pdf_url;
                        if (!u)
                            return [2 /*return*/];
                        href = "".concat(joinUrl(cfg.base, u), "?format=html");
                        window.open(href, "_blank");
                        return [2 /*return*/];
                }
            });
        }); }}>Open Latest WTN (HTML)</button>

        <button disabled={busy} onClick={function () { return __awaiter(_this, void 0, void 0, function () {
            var r, u, href;
            var _a, _b;
            return __generator(this, function (_c) {
                switch (_c.label) {
                    case 0: return [4 /*yield*/, run("__debug/wtns", function () { return api_1.api.latestWtns(1); })];
                    case 1:
                        r = _c.sent();
                        u = (_b = (_a = r === null || r === void 0 ? void 0 : r.items) === null || _a === void 0 ? void 0 : _a[0]) === null || _b === void 0 ? void 0 : _b.pdf_url;
                        if (!u)
                            return [2 /*return*/];
                        href = "".concat(joinUrl(cfg.base, u), "?format=pdf");
                        window.open(href, "_blank");
                        return [2 /*return*/];
                }
            });
        }); }}>Open Latest WTN (PDF)</button>
        </div>
      </section>

      {/* Admin CRUD */}
      <section className="card">
        <h2>Admin: Drivers & Vehicles</h2>
        <div className="grid3">
          <label>Driver
            <select value={driverId} onChange={function (e) { return setDriverId(e.target.value); }}>
              <option value="">-- select driver --</option>
              {drivers.map(function (d) { return <option key={d.id} value={d.id}>{driverLabel(d)}</option>; })}
            </select>
          </label>
          <label>Vehicle
            <select value={vehId} onChange={function (e) { return setVehId(e.target.value); }}>
              <option value="">-- select vehicle --</option>
              {vehicles.map(function (v) { return <option key={v.id} value={v.id}>{vehicleLabel(v)}</option>; })}
            </select>
          </label>
          <div className="row">
            <button onClick={seedDriver}>+ Driver</button>
            <button onClick={seedVehicle}>+ Vehicle</button>
          </div>
        </div>

        {/* Driver editor */}
        {drvEdit && (<div style={{ marginTop: 12 }}>
            <h3 style={{ margin: "8px 0" }}>Edit Driver</h3>
            <div className="grid3">
              <label>Name
                <input value={drvEdit.name} onChange={function (e) { setDrvEdit(__assign(__assign({}, drvEdit), { name: e.target.value })); setDrvErrs(__assign(__assign({}, drvErrs), { name: "" })); }}/>
                {drvErrs.name ? <small style={{ color: "#f39" }}>{drvErrs.name}</small> : null}
              </label>
              <label>Phone<input value={(_j = drvEdit.phone) !== null && _j !== void 0 ? _j : ""} onChange={function (e) { return setDrvEdit(__assign(__assign({}, drvEdit), { phone: e.target.value })); }}/></label>
              <label>License #<input value={(_k = drvEdit.license_no) !== null && _k !== void 0 ? _k : ""} onChange={function (e) { return setDrvEdit(__assign(__assign({}, drvEdit), { license_no: e.target.value })); }}/></label>
            </div>
            <div className="row" style={{ marginTop: 8 }}>
              <label className="row"><input type="checkbox" checked={drvEdit.active} onChange={function (e) { return setDrvEdit(__assign(__assign({}, drvEdit), { active: e.target.checked })); }}/> Active</label>
              <button disabled={!!validateDriver(drvEdit).name} onClick={saveDriver}>Save</button>
              <button className="ghost" onClick={deleteDriver}>Delete</button>
            </div>
          </div>)}

        {/* Vehicle editor */}
        {vehEdit && (<div style={{ marginTop: 12 }}>
            <h3 style={{ margin: "8px 0" }}>Edit Vehicle</h3>
            <div className="grid3">
              <label>Reg No
                <input value={vehEdit.reg_no} onChange={function (e) { setVehEdit(__assign(__assign({}, vehEdit), { reg_no: e.target.value })); setVehErrs(__assign(__assign({}, vehErrs), { reg_no: "" })); }}/>
                {vehErrs.reg_no ? <small style={{ color: "#f39" }}>{vehErrs.reg_no}</small> : null}
              </label>
              <label>Make<input value={(_l = vehEdit.make) !== null && _l !== void 0 ? _l : ""} onChange={function (e) { return setVehEdit(__assign(__assign({}, vehEdit), { make: e.target.value })); }}/></label>
              <label>Model<input value={(_m = vehEdit.model) !== null && _m !== void 0 ? _m : ""} onChange={function (e) { return setVehEdit(__assign(__assign({}, vehEdit), { model: e.target.value })); }}/></label>
            </div>
            <div className="row" style={{ marginTop: 8 }}>
              <label className="row"><input type="checkbox" checked={vehEdit.active} onChange={function (e) { return setVehEdit(__assign(__assign({}, vehEdit), { active: e.target.checked })); }}/> Active</label>
              <button disabled={!!validateVehicle(vehEdit).reg_no} onClick={saveVehicle}>Save</button>
              <button className="ghost" onClick={deleteVehicle}>Delete</button>
            </div>
          </div>)}
      </section>

      {/* Skip create */}
      <SkipCreationForm_1.default />

      <section className="card">
        <h2>Seed & Driver Flow</h2>
        <div className="grid3">
          <label>QR<input value={qr} onChange={function (e) { return setQr(e.target.value); }}/></label>
          <label>Zones A/B/C<div className="row">
            <input value={zoneA} onChange={function (e) { return setZoneA(e.target.value); }} style={{ width: "33%" }}/>
            <input value={zoneB} onChange={function (e) { return setZoneB(e.target.value); }} style={{ width: "33%" }}/>
            <input value={zoneC} onChange={function (e) { return setZoneC(e.target.value); }} style={{ width: "33%" }}/>
          </div></label>
          <label>Destination<input value={destName} onChange={function (e) { return setDestName(e.target.value); }}/></label>
        </div>
        <div className="grid3">
          <label>Driver name<input value={driverName} onChange={function (e) { return setDriverName(e.target.value); }}/></label>
          <label>Vehicle reg<input value={vehReg} onChange={function (e) { return setVehReg(e.target.value); }}/></label>
          <label>Dest. Type<select value={destType} onChange={function (e) { return setDestType(e.target.value); }}>
            <option>RECYCLING</option><option>LANDFILL</option><option>TRANSFER</option>
          </select></label>
        </div>
        <div className="grid3">
          <label>Gross (kg)<input type="number" value={gross} onChange={function (e) { return setGross(safeNum(e.target.value)); }}/></label>
          <label>Tare (kg)<input type="number" value={tare} onChange={function (e) { return setTare(safeNum(e.target.value)); }}/></label>
          <label>Site ID<input value={siteId} onChange={function (e) { return setSiteId(e.target.value); }}/></label>
        </div>
        <div className="row wrap" style={{ marginTop: 8 }}>
          <button disabled={busy} onClick={function () { return run("DEV ensure-skip", function () { return api_1.api.ensureSkipDev(qr); }); }}>Seed skip</button>
          <button disabled={busy} onClick={function () { return run("driver/scan", function () { return api_1.api.scan(qr); }); }}>Scan</button>
          <button disabled={busy} onClick={function () { return run("driver/deliver-empty", function () { return api_1.api.deliverEmpty({ skip_qr: qr, to_zone_id: zoneC, driver_name: driverName, vehicle_reg: vehReg }); }); }}>Deliver Empty</button>
          <button disabled={busy} onClick={function () { return run("driver/relocate-empty", function () { return api_1.api.relocateEmpty({ skip_qr: qr, from_zone_id: zoneA, to_zone_id: zoneB, driver_name: driverName }); }); }}>Relocate Empty</button>
          <button disabled={busy} onClick={function () { return run("driver/collect-full", function () { return api_1.api.collectFull({ skip_qr: qr, destination_type: destType, destination_name: destName, weight_source: "WEIGHBRIDGE", gross_kg: gross, tare_kg: tare, driver_name: driverName, site_id: siteId, vehicle_reg: vehReg }); }); }}>Collect Full</button>
          <button disabled={busy} onClick={function () { return run("driver/return-empty", function () { return api_1.api.returnEmpty({ skip_qr: qr, to_zone_id: zoneC, driver_name: driverName }); }); }}>Return Empty</button>
          <button className="primary" disabled={busy} onClick={runAll}>Run Full Flow</button>
        </div>
      </section>

      <section className="card">
        <h2>Results</h2>
        {out.length === 0 ? <p className="muted">No calls yet.</p> : null}
        {out.map(function (o, i) {
            var wtnUrl = findWtnUrl(o.payload);
            var htmlUrl = wtnUrl ? "".concat(joinUrl(cfg.base, wtnUrl), "?format=html") : null;
            var pdfUrl = wtnUrl ? "".concat(joinUrl(cfg.base, wtnUrl), "?format=pdf") : null;
            return (<details key={i} open={i === 0} className="result">
              <summary><strong>{o.title}</strong> <span className="muted">at {o.at}</span></summary>
              <pre>{(0, api_1.pretty)(o.payload)}</pre>
              {wtnUrl && (<div className="row" style={{ gap: 8, marginTop: 8 }}>
                  <a className="btn" href={htmlUrl} target="_blank" rel="noreferrer">Open WTN (HTML)</a>
                  <a className="btn" href={pdfUrl} target="_blank" rel="noreferrer">Open PDF</a>
                </div>)}
            </details>);
        })}
      </section>
    </div>);
}
