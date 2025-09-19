"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = DriverMePage;
var react_1 = require("react");
var api_1 = require("../api");
function DriverMePage() {
    var _a;
    var _b = (0, react_1.useState)(null), data = _b[0], setData = _b[1];
    var _c = (0, react_1.useState)(null), err = _c[0], setErr = _c[1];
    (0, react_1.useEffect)(function () {
        (0, api_1.getDriverMe)().then(setData).catch(function (e) { return setErr(String(e)); });
    }, []);
    if (err)
        return <div className="p-4 text-red-600">Error: {err}</div>;
    if (!data)
        return <div className="p-4">Loading…</div>;
    return (<div className="p-4 space-y-3">
      <h1 className="text-xl font-semibold">Driver Status</h1>
      <div className="rounded-xl border p-4">
        <div><b>User</b>: {data.user_id}</div>
        <div><b>Status</b>: {data.status}</div>
        <div><b>Updated</b>: {new Date(data.updated_at).toLocaleString()}</div>
      </div>

      <h2 className="text-lg font-medium mt-4">Open Assignment</h2>
      {!data.open_assignment ? (<div className="text-slate-500">None</div>) : (<div className="rounded-xl border p-4">
          <div><b>ID</b>: {data.open_assignment.id}</div>
          <div><b>Skip</b>: {data.open_assignment.skip_id}</div>
          <div><b>QR</b>: {(_a = data.open_assignment.skip_qr_code) !== null && _a !== void 0 ? _a : "—"}</div>
          <div><b>Status</b>: {data.open_assignment.status}</div>
        </div>)}
    </div>);
}
