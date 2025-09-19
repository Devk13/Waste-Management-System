"use strict";
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        if (typeof b !== "function" && b !== null)
            throw new TypeError("Class extends value " + String(b) + " is not a constructor or null");
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
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
exports.api = exports.ApiError = void 0;
exports.setConfig = setConfig;
exports.getConfig = getConfig;
exports.pretty = pretty;
exports.adminCreateSkip = adminCreateSkip;
exports.getDriverMe = getDriverMe;
exports.searchFacilities = searchFacilities;
exports.searchZones = searchZones;
exports.dropAtFacility = dropAtFacility;
// ======================================================================
// path: frontend/src/api.ts
// ======================================================================
var axios_1 = require("axios");
var LS_KEY = "wm_dev_console_cfg";
function loadConfig() {
    var _a;
    try {
        var raw = localStorage.getItem(LS_KEY);
        if (raw)
            return JSON.parse(raw);
    }
    catch (_b) { }
    return { base: ((_a = import.meta.env) === null || _a === void 0 ? void 0 : _a.VITE_API_BASE) || window.location.origin, apiKey: "", adminKey: "" };
}
function saveConfig(c) { localStorage.setItem(LS_KEY, JSON.stringify(c)); }
var cfg = loadConfig();
var client = createClient(cfg);
function createClient(c) {
    var inst = axios_1.default.create({ baseURL: c.base.replace(/\/+$/, ""), timeout: 20000 });
    inst.interceptors.request.use(function (req) {
        var url = (req.url || "").toLowerCase();
        var h = req.headers || {};
        var needsDriverKey = url.startsWith("/driver") || url.includes("/ensure-skip");
        var needsAdminKey = url.startsWith("/admin") || url.startsWith("/skips/_seed");
        if (needsDriverKey && c.apiKey)
            h["X-API-Key"] = c.apiKey;
        if (needsAdminKey && c.adminKey)
            h["X-API-Key"] = c.adminKey;
        req.headers = h;
        return req;
    });
    return inst;
}
function setConfig(next) { cfg = next; saveConfig(cfg); client = createClient(cfg); }
function getConfig() { return cfg; }
function get(url, config) {
    return __awaiter(this, void 0, void 0, function () { return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, client.get(url, config)];
            case 1: return [2 /*return*/, (_a.sent()).data];
        }
    }); });
}
function post(url, body, config) {
    return __awaiter(this, void 0, void 0, function () { return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, client.post(url, body !== null && body !== void 0 ? body : {}, config)];
            case 1: return [2 /*return*/, (_a.sent()).data];
        }
    }); });
}
function patch(url, body) {
    return __awaiter(this, void 0, void 0, function () { return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, client.patch(url, body !== null && body !== void 0 ? body : {})];
            case 1: return [2 /*return*/, (_a.sent()).data];
        }
    }); });
}
function del(url) {
    return __awaiter(this, void 0, void 0, function () { return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, client.delete(url)];
            case 1: return [2 /*return*/, (_a.sent()).data];
        }
    }); });
}
var ApiError = /** @class */ (function (_super) {
    __extends(ApiError, _super);
    function ApiError(message, code, fields) {
        var _this = _super.call(this, message) || this;
        _this.code = code;
        _this.fields = fields;
        return _this;
    }
    return ApiError;
}(Error));
exports.ApiError = ApiError;
function parseApiError(e) {
    var _a, _b, _c, _d, _e;
    var code = (_b = (_a = e === null || e === void 0 ? void 0 : e.response) === null || _a === void 0 ? void 0 : _a.status) !== null && _b !== void 0 ? _b : 0;
    var data = (_d = (_c = e === null || e === void 0 ? void 0 : e.response) === null || _c === void 0 ? void 0 : _c.data) !== null && _d !== void 0 ? _d : {};
    // FastAPI validation array → field map
    var as422 = function (d) {
        var out = {};
        if (Array.isArray(d === null || d === void 0 ? void 0 : d.detail)) {
            for (var _i = 0, _a = d.detail; _i < _a.length; _i++) {
                var it = _a[_i];
                var loc = ((it === null || it === void 0 ? void 0 : it.loc) || []).slice(1).join(".") || "non_field";
                var msg = (it === null || it === void 0 ? void 0 : it.msg) || (it === null || it === void 0 ? void 0 : it.message) || "Invalid value";
                out[loc] = msg;
            }
        }
        return out;
    };
    function createClient(c) {
        var inst = axios_1.default.create({ baseURL: c.base.replace(/\/+$/, ""), timeout: 20000 });
        inst.interceptors.request.use(function (req) {
            var url = (req.url || "").toLowerCase();
            var h = req.headers || {};
            var needsDriverKey = url.startsWith("/driver") || url.includes("/ensure-skip");
            var needsAdminKey = url.startsWith("/admin") || url.startsWith("/skips/_seed") || url.startsWith("/__debug");
            if (needsDriverKey && c.apiKey)
                h["X-API-Key"] = c.apiKey;
            if (needsAdminKey && c.adminKey)
                h["X-API-Key"] = c.adminKey;
            req.headers = h;
            return req;
        });
        return inst;
    }
    // Common server shapes
    var message = ((_e = data === null || data === void 0 ? void 0 : data.detail) === null || _e === void 0 ? void 0 : _e.message) || (data === null || data === void 0 ? void 0 : data.detail) || (data === null || data === void 0 ? void 0 : data.error) || (e === null || e === void 0 ? void 0 : e.message) || "Request failed";
    var fields;
    if (code === 422)
        fields = as422(data);
    if (code === 409) {
        // Try infer unique field
        var txt = String(message).toLowerCase();
        if (txt.includes("reg") || txt.includes("vehicle"))
            fields = { reg_no: "Registration already exists" };
        if (txt.includes("driver") || txt.includes("name"))
            fields = { name: "Driver with this name already exists" };
        message = "Duplicate value";
    }
    return new ApiError(message, code, fields);
}
// ---------- API surface ----------
exports.api = {
    // debug/meta
    health: function () { return get("/_meta/ping"); },
    routes: function () { return get("/_debug/routes"); },
    mounts: function () { return get("/_debug/mounts"); },
    skipsSmoke: function () { return get("/skips/__smoke"); },
    versions: function () { return get("/meta/versions"); },
    latestWtns: function (limit) {
        if (limit === void 0) { limit = 5; }
        return get("/__debug/wtns?limit=".concat(limit));
    }, // admin-gated in prod
    meta: function () { return __awaiter(void 0, void 0, void 0, function () {
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    _b.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, get("/meta/config")];
                case 1: return [2 /*return*/, _b.sent()];
                case 2:
                    _a = _b.sent();
                    return [2 /*return*/, { skip: { colors: { green: { label: "Recycling" } }, sizes: { sizes_m3: [6, 8, 12] } } }];
                case 3: return [2 /*return*/];
            }
        });
    }); },
    // dev seed
    ensureSkipDev: function (qr) { return __awaiter(void 0, void 0, void 0, function () {
        var e_1;
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    _b.trys.push([0, 2, , 5]);
                    return [4 /*yield*/, post("/driver/dev/ensure-skip", { qr_code: qr, qr: qr })];
                case 1: return [2 /*return*/, _b.sent()];
                case 2:
                    e_1 = _b.sent();
                    if (!(((_a = e_1 === null || e_1 === void 0 ? void 0 : e_1.response) === null || _a === void 0 ? void 0 : _a.status) === 422)) return [3 /*break*/, 4];
                    return [4 /*yield*/, get("/driver/dev/ensure-skip?qr=".concat(encodeURIComponent(qr)))];
                case 3: return [2 /*return*/, _b.sent()];
                case 4: throw parseApiError(e_1);
                case 5: return [2 /*return*/];
            }
        });
    }); },
    // driver flow
    scan: function (qr) { return __awaiter(void 0, void 0, void 0, function () {
        var e_2;
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    _b.trys.push([0, 2, , 5]);
                    return [4 /*yield*/, get("/driver/scan?qr=".concat(encodeURIComponent(qr)))];
                case 1: return [2 /*return*/, _b.sent()];
                case 2:
                    e_2 = _b.sent();
                    if (![400, 422].includes((_a = e_2 === null || e_2 === void 0 ? void 0 : e_2.response) === null || _a === void 0 ? void 0 : _a.status)) return [3 /*break*/, 4];
                    return [4 /*yield*/, get("/driver/scan?q=".concat(encodeURIComponent(qr)))];
                case 3: return [2 /*return*/, _b.sent()];
                case 4: throw parseApiError(e_2);
                case 5: return [2 /*return*/];
            }
        });
    }); },
    deliverEmpty: function (p) { return __awaiter(void 0, void 0, void 0, function () {
        var e_3;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, post("/driver/deliver-empty", p)];
                case 1: return [2 /*return*/, _a.sent()];
                case 2:
                    e_3 = _a.sent();
                    throw parseApiError(e_3);
                case 3: return [2 /*return*/];
            }
        });
    }); },
    relocateEmpty: function (p) { return __awaiter(void 0, void 0, void 0, function () {
        var e_4;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, post("/driver/relocate-empty", p)];
                case 1: return [2 /*return*/, _a.sent()];
                case 2:
                    e_4 = _a.sent();
                    throw parseApiError(e_4);
                case 3: return [2 /*return*/];
            }
        });
    }); },
    collectFull: function (p) { return __awaiter(void 0, void 0, void 0, function () {
        var e_5;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, post("/driver/collect-full", p)];
                case 1: return [2 /*return*/, _a.sent()];
                case 2:
                    e_5 = _a.sent();
                    throw parseApiError(e_5);
                case 3: return [2 /*return*/];
            }
        });
    }); },
    returnEmpty: function (p) { return __awaiter(void 0, void 0, void 0, function () {
        var e_6;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, post("/driver/return-empty", p)];
                case 1: return [2 /*return*/, _a.sent()];
                case 2:
                    e_6 = _a.sent();
                    throw parseApiError(e_6);
                case 3: return [2 /*return*/];
            }
        });
    }); },
    // admin: drivers
    listDrivers: function () { return get("/admin/drivers"); },
    createDriver: function (p) { return __awaiter(void 0, void 0, void 0, function () {
        var e_7;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, post("/admin/drivers", p)];
                case 1: return [2 /*return*/, _a.sent()];
                case 2:
                    e_7 = _a.sent();
                    throw parseApiError(e_7);
                case 3: return [2 /*return*/];
            }
        });
    }); },
    updateDriver: function (id, p) { return __awaiter(void 0, void 0, void 0, function () {
        var e_8;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, patch("/admin/drivers/".concat(id), p)];
                case 1: return [2 /*return*/, _a.sent()];
                case 2:
                    e_8 = _a.sent();
                    throw parseApiError(e_8);
                case 3: return [2 /*return*/];
            }
        });
    }); },
    deleteDriver: function (id) { return __awaiter(void 0, void 0, void 0, function () {
        var e_9;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, del("/admin/drivers/".concat(id))];
                case 1: return [2 /*return*/, _a.sent()];
                case 2:
                    e_9 = _a.sent();
                    throw parseApiError(e_9);
                case 3: return [2 /*return*/];
            }
        });
    }); },
    // admin: vehicles
    listVehicles: function () { return get("/admin/vehicles"); },
    createVehicle: function (p) { return __awaiter(void 0, void 0, void 0, function () {
        var e_10;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, post("/admin/vehicles", p)];
                case 1: return [2 /*return*/, _a.sent()];
                case 2:
                    e_10 = _a.sent();
                    throw parseApiError(e_10);
                case 3: return [2 /*return*/];
            }
        });
    }); },
    updateVehicle: function (id, p) { return __awaiter(void 0, void 0, void 0, function () {
        var e_11;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, patch("/admin/vehicles/".concat(id), p)];
                case 1: return [2 /*return*/, _a.sent()];
                case 2:
                    e_11 = _a.sent();
                    throw parseApiError(e_11);
                case 3: return [2 /*return*/];
            }
        });
    }); },
    deleteVehicle: function (id) { return __awaiter(void 0, void 0, void 0, function () {
        var e_12;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, del("/admin/vehicles/".concat(id))];
                case 1: return [2 /*return*/, _a.sent()];
                case 2:
                    e_12 = _a.sent();
                    throw parseApiError(e_12);
                case 3: return [2 /*return*/];
            }
        });
    }); },
};
function pretty(x) { try {
    return JSON.stringify(x, null, 2);
}
catch (_a) {
    return String(x);
} }
function adminCreateSkip(p) {
    return __awaiter(this, void 0, void 0, function () {
        var e_13;
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    _b.trys.push([0, 2, , 5]);
                    return [4 /*yield*/, post("/skips/_seed", p, { headers: { "X-API-Key": getConfig().adminKey || "" } })];
                case 1: return [2 /*return*/, _b.sent()];
                case 2:
                    e_13 = _b.sent();
                    if (![401, 403, 404, 405].includes((_a = e_13 === null || e_13 === void 0 ? void 0 : e_13.response) === null || _a === void 0 ? void 0 : _a.status)) return [3 /*break*/, 4];
                    return [4 /*yield*/, post("/driver/dev/ensure-skip", { qr_code: p.qr, qr: p.qr }, { headers: { "X-API-Key": getConfig().adminKey || getConfig().apiKey || "" } })];
                case 3: return [2 /*return*/, _b.sent()];
                case 4: throw parseApiError(e_13);
                case 5: return [2 /*return*/];
            }
        });
    });
}
function getDriverMe() {
    return __awaiter(this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            return [2 /*return*/, { id: "drv-demo", name: "Demo Driver" }];
        });
    });
}
function searchFacilities(_q) {
    return __awaiter(this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            return [2 /*return*/, [{ id: "ECO_MRF", name: "ECO MRF" }]];
        });
    });
}
function searchZones(_q) {
    return __awaiter(this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            return [2 /*return*/, [
                    { id: "ZONE_A", name: "ZONE_A" },
                    { id: "ZONE_B", name: "ZONE_B" },
                    { id: "ZONE_C", name: "ZONE_C" },
                ]];
        });
    });
}
function dropAtFacility(p) {
    return __awaiter(this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, exports.api.collectFull({
                        skip_qr: p.skip_qr,
                        destination_type: "TRANSFER",
                        destination_name: p.facility_name,
                        weight_source: p.weight_source,
                        gross_kg: p.gross_kg,
                        tare_kg: p.tare_kg,
                        net_kg: p.net_kg,
                        driver_name: p.driver_name,
                        vehicle_reg: p.vehicle_reg,
                        site_id: p.site_id,
                    })];
                case 1: return [2 /*return*/, _a.sent()];
            }
        });
    });
}
