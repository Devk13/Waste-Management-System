"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = WtnPrompt;
var react_1 = require("react");
function WtnPrompt() {
    var _a = react_1.default.useState(null), url = _a[0], setUrl = _a[1];
    var _b = react_1.default.useState(undefined), id = _b[0], setId = _b[1];
    var _c = react_1.default.useState(function () {
        var v = localStorage.getItem('wtn:autoOpen');
        return v === null || v === '1';
    }), autoOpen = _c[0], setAutoOpen = _c[1];
    react_1.default.useEffect(function () {
        var onReady = function (e) {
            var detail = e.detail;
            if (detail === null || detail === void 0 ? void 0 : detail.url) {
                setUrl(detail.url);
                setId(detail.id);
            }
        };
        window.addEventListener('wtn:ready', onReady);
        return function () { return window.removeEventListener('wtn:ready', onReady); };
    }, []);
    react_1.default.useEffect(function () {
        localStorage.setItem('wtn:autoOpen', autoOpen ? '1' : '0');
    }, [autoOpen]);
    if (!url)
        return null;
    return (<div style={{
            position: 'fixed',
            right: 16,
            bottom: 16,
            maxWidth: 420,
            zIndex: 50,
            boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
            borderRadius: 12,
            padding: 14,
            background: '#111827',
            color: 'white',
        }} role="status" aria-live="polite">
      <div style={{ fontWeight: 600, marginBottom: 6 }}>
        Waste Transfer Note {id ? "\u00B7 ".concat(id) : ''}
      </div>
      <div style={{ opacity: 0.85, fontSize: 14, marginBottom: 10 }}>
        A WTN PDF is ready from the last <em>collect-full</em>.
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <a href={url} target="_blank" rel="noopener noreferrer" style={{
            padding: '8px 12px',
            borderRadius: 8,
            background: 'white',
            color: '#111827',
            textDecoration: 'none',
            fontWeight: 600,
        }}>
          Open PDF
        </a>
        <button onClick={function () {
            var _a;
            (_a = navigator.clipboard) === null || _a === void 0 ? void 0 : _a.writeText(url).catch(function () { });
        }} style={{
            padding: '8px 12px',
            borderRadius: 8,
            background: '#e5e7eb',
            color: '#111827',
            fontWeight: 600,
            border: 'none',
            cursor: 'pointer',
        }}>
          Copy Link
        </button>
        <label style={{ display: 'inline-flex', gap: 8, alignItems: 'center', fontSize: 13 }}>
          <input type="checkbox" checked={autoOpen} onChange={function (e) { return setAutoOpen(e.target.checked); }}/>
          Auto-open next time
        </label>
        <button onClick={function () { return setUrl(null); }} style={{
            marginLeft: 'auto',
            padding: 6,
            borderRadius: 8,
            background: 'transparent',
            color: '#9ca3af',
            border: '1px solid #374151',
            cursor: 'pointer',
        }} aria-label="Dismiss WTN prompt" title="Dismiss">
          ×
        </button>
      </div>
    </div>);
}
