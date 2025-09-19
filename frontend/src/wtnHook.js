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
var ORIG_FETCH = window.fetch.bind(window);
function toAbsolute(url, base) {
    try {
        return new URL(url, base !== null && base !== void 0 ? base : window.location.origin).toString();
    }
    catch (_a) {
        return url;
    }
}
function shouldAutoOpen() {
    var v = localStorage.getItem('wtn:autoOpen');
    return v === null || v === '1';
}
window.fetch = function (input, init) { return __awaiter(void 0, void 0, void 0, function () {
    var res, urlStr_1, clone, contentType, data, wtnPath, wtnId, base, abs, _a;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0: return [4 /*yield*/, ORIG_FETCH(input, init)];
            case 1:
                res = _b.sent();
                _b.label = 2;
            case 2:
                _b.trys.push([2, 5, , 6]);
                urlStr_1 = typeof input === 'string' ? input : input.toString();
                if (!urlStr_1.includes('/driver/collect-full')) return [3 /*break*/, 4];
                clone = res.clone();
                contentType = clone.headers.get('content-type') || '';
                if (!contentType.includes('application/json')) return [3 /*break*/, 4];
                return [4 /*yield*/, clone.json().catch(function () { return null; })];
            case 3:
                data = _b.sent();
                wtnPath = data === null || data === void 0 ? void 0 : data.wtn_pdf_url;
                wtnId = data === null || data === void 0 ? void 0 : data.wtn_id;
                if (wtnPath) {
                    base = (function () {
                        try {
                            return new URL(urlStr_1).origin;
                        }
                        catch (_a) {
                            return undefined;
                        }
                    })();
                    abs = toAbsolute(wtnPath, base);
                    // Notify UI listeners
                    window.dispatchEvent(new CustomEvent('wtn:ready', { detail: { url: abs, id: wtnId } }));
                    if (shouldAutoOpen()) {
                        // Open in new tab; 'noopener' for safety
                        window.open(abs, '_blank', 'noopener,noreferrer');
                    }
                }
                _b.label = 4;
            case 4: return [3 /*break*/, 6];
            case 5:
                _a = _b.sent();
                return [3 /*break*/, 6];
            case 6: return [2 /*return*/, res];
        }
    });
}); };
