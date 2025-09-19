"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ResultsPanel = void 0;
// path: frontend/src/components/ResultsPanel.tsx
var react_1 = require("react");
var WtnLink_1 = require("./WtnLink");
var ResultsPanel = function (_a) {
    var baseUrl = _a.baseUrl, title = _a.title, payload = _a.payload;
    var wtnUrl = (0, WtnLink_1.findWtnUrl)(payload);
    return (<div className="rounded-2xl border border-slate-700 p-4 mt-4">
      <div className="font-semibold mb-2">{title}</div>
      <pre className="text-sm whitespace-pre-wrap break-all">
        {JSON.stringify(payload, null, 2)}
      </pre>

      {wtnUrl && (<WtnLink_1.WtnLink baseUrl={baseUrl} wtnPdfUrl={wtnUrl} className="flex gap-2 mt-3"/>)}
    </div>);
};
exports.ResultsPanel = ResultsPanel;
