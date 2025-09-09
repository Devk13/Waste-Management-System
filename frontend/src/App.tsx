// path: frontend/src/App.tsx
import React from "react";
import LabelsAdmin from "./pages/LabelsAdmin";

export default function App() {
  return (
    <div className="min-h-screen bg-slate-100">
      <header className="sticky top-0 z-10 border-b bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between p-4">
          <h1 className="text-lg font-semibold">WMMS • Admin</h1>
          <div className="text-xs text-slate-500">Create QR Labels</div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl p-4">
        <LabelsAdmin />
      </main>
    </div>
  );
}
