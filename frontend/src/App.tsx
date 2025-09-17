import React from "react";
import { HashRouter, Routes, Route, Link, Navigate } from "react-router-dom";
import DriverMe from "./pages/DriverMe";
import LabelsAdmin from "./pages/LabelsAdmin";
import WtnAdmin from "./pages/WtnAdmin";

export default function App() {
  return (
    // HashRouter avoids server-side route config on static hosts (e.g., Render static)
    <HashRouter>
      <nav style={{ padding: 12, borderBottom: "1px solid #e5e7eb", display: "flex", gap: 12 }}>
        <Link to="/">Driver</Link>
        <Link to="/admin/labels">Labels</Link>
        <Link to="/admin/wtn">WTN</Link>
      </nav>
      <Routes>
        <Route path="/" element={<DriverMe />} />
        <Route path="/admin/labels" element={<LabelsAdmin />} />
        <Route path="/admin/wtn" element={<WtnAdmin />} />
        {/* fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  );
}
