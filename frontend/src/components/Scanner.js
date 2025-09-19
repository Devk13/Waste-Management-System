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
exports.default = Scanner;
// path: frontend/src/components/Scanner.tsx
var react_1 = require("react");
var react_qr_scanner_1 = require("@yudiel/react-qr-scanner");
var lucide_react_1 = require("lucide-react");
function Scanner(_a) {
    var _this = this;
    var onScan = _a.onScan;
    var _b = (0, react_1.useState)(true), enabled = _b[0], setEnabled = _b[1];
    var _c = (0, react_1.useState)(null), err = _c[0], setErr = _c[1];
    var _d = (0, react_1.useState)(''), manual = _d[0], setManual = _d[1];
    // debounced duplicate frame filter
    var lastTextRef = (0, react_1.useRef)('');
    var lastTsRef = (0, react_1.useRef)(0);
    var handleResult = (0, react_1.useCallback)(function (raw) {
        if (!raw)
            return;
        var now = Date.now();
        if (raw === lastTextRef.current && now - lastTsRef.current < 1500)
            return;
        lastTextRef.current = raw;
        lastTsRef.current = now;
        onScan(raw);
    }, [onScan]);
    var handlePaste = function () { return __awaiter(_this, void 0, void 0, function () {
        var text, _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    _b.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, navigator.clipboard.readText()];
                case 1:
                    text = _b.sent();
                    if (text) {
                        setManual(text);
                        handleResult(text);
                    }
                    return [3 /*break*/, 3];
                case 2:
                    _a = _b.sent();
                    setErr('Clipboard is unavailable');
                    return [3 /*break*/, 3];
                case 3: return [2 /*return*/];
            }
        });
    }); };
    var handleSubmitManual = function (e) {
        e.preventDefault();
        if (manual.trim())
            handleResult(manual.trim());
    };
    // Optional: remember camera toggle
    (0, react_1.useEffect)(function () { try {
        localStorage.setItem('scan:cam', String(enabled));
    }
    catch (_a) { } }, [enabled]);
    (0, react_1.useEffect)(function () {
        try {
            var v = localStorage.getItem('scan:cam');
            if (v !== null)
                setEnabled(v === 'true');
        }
        catch (_a) { }
    }, []);
    // If your editor still complains about props because the old type is cached,
    // this cast silences it while the uninstall settles:
    var AnyScanner = react_qr_scanner_1.Scanner;
    return (<div className="rounded-2xl border bg-white shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b bg-slate-50">
        <div className="flex items-center gap-2"><lucide_react_1.Camera className="w-4 h-4"/> Scanner</div>
        <div className="flex items-center gap-2">
          <button className="btn btn-ghost" title={enabled ? 'Pause' : 'Start'} onClick={function () { return setEnabled(function (v) { return !v; }); }}>
            {enabled ? <lucide_react_1.Pause className="w-4 h-4"/> : <lucide_react_1.Play className="w-4 h-4"/>}
          </button>
          <button className="btn btn-ghost" title="Reset last" onClick={function () { return (lastTextRef.current = '', lastTsRef.current = 0); }}>
            <lucide_react_1.RefreshCcw className="w-4 h-4"/>
          </button>
        </div>
      </div>

      <div className="p-3">
        <div className="aspect-video rounded-xl overflow-hidden bg-black/5">
          {enabled && (<AnyScanner onResult={function (text) {
                return handleResult(typeof text === 'string' ? text : text === null || text === void 0 ? void 0 : text.rawValue);
            }} onError={function (e) { return setErr((e === null || e === void 0 ? void 0 : e.message) || 'Camera error'); }} styles={{ container: { width: '100%', height: '100%' } }}/>)}
        </div>

        {err && <div className="mt-2 rounded-md bg-rose-50 text-rose-700 px-3 py-2 text-sm">{err}</div>}

        {/* Manual fallback */}
        <form onSubmit={handleSubmitManual} className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto_auto]">
          <input className="input" placeholder="Paste or type code / full URL" value={manual} onChange={function (e) { return setManual(e.target.value); }}/>
          <button type="button" className="btn" onClick={handlePaste} title="Paste from clipboard">
            <lucide_react_1.ClipboardPaste className="w-4 h-4 mr-1"/> Paste
          </button>
          <button className="btn" type="submit">Use</button>
        </form>
        <p className="text-xs text-slate-500 mt-1">
          Tip: you can scan a QR or paste a full deep link like <code>/driver/qr/SK-1234</code>.
        </p>
      </div>
    </div>);
}
