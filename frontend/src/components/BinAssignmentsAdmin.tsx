// ===========================
// frontend/src/components/BinAssignmentsAdmin.tsx
// ===========================
import React, { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "../api";
import { toast } from "../ui/toast";

type Contractor = { id: string; name: string };
type BinAssignment = {
  id: string;
  contractor_id: string;
  zone_id?: string;       // free text zone/site identifier
  bin_size?: string;      // e.g. "6m3", "240L"
  color?: string;         // e.g. "green"
  active?: boolean;
  notes?: string;
};

export default function BinAssignmentsAdmin() {
  const [contractors, setContractors] = useState<Contractor[]>([]);
  const [items, setItems] = useState<BinAssignment[]>([]);
  const [selId, setSelId] = useState<string>("");
  const [edit, setEdit] = useState<BinAssignment | null>(null);
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);

  const selected = useMemo(
    () => items.find((x) => x.id === selId) ?? null,
    [items, selId]
  );

  useEffect(() => {
    (async () => {
      try {
        const [cons, list] = await Promise.all([
          api.listContractors(),
          api.listBinAssignments(),
        ]);
        setContractors(cons);
        setItems(list);
      } catch (e: any) {
        toast.error("Failed to load assignments", e?.message);
      }
    })();
  }, []);

  useEffect(() => {
    if (selected) {
      setEdit({
        id: selected.id,
        contractor_id: selected.contractor_id,
        zone_id: selected.zone_id ?? "",
        bin_size: selected.bin_size ?? "",
        color: selected.color ?? "",
        active: Boolean(selected.active ?? true),
        notes: selected.notes ?? "",
      });
    } else {
      setEdit(null);
    }
    setErrs({});
  }, [selected]);

  const validate = (p: Partial<BinAssignment>) => {
    const e: Record<string, string> = {};
    if (!p.contractor_id) e.contractor_id = "Contractor required";
    return e;
  };

  const createItem = async () => {
    const contractor_id = prompt("Contractor ID (pick from dropdown after create)") || "";
    if (!contractor_id) return;
    setBusy(true);
    try {
      const r = await api.createBinAssignment({ contractor_id });
      setItems(await api.listBinAssignments());
      setSelId(r.id);
      toast.success("Assignment created");
    } catch (e: any) {
      toast.error((e as ApiError).message || "Create failed");
    } finally {
      setBusy(false);
    }
  };

  const save = async () => {
    if (!selId || !edit) return;
    const v = validate(edit);
    setErrs(v);
    if (Object.keys(v).length) return;

    setBusy(true);
    try {
      await api.updateBinAssignment(selId, {
        contractor_id: edit.contractor_id,
        zone_id: edit.zone_id ?? "",
        bin_size: edit.bin_size ?? "",
        color: edit.color ?? "",
        active: Boolean(edit.active),
        notes: edit.notes ?? "",
      });
      setItems(await api.listBinAssignments());
      toast.success("Saved");
    } catch (e: any) {
      const ae = e as ApiError;
      if (ae.fields) setErrs({ ...errs, ...ae.fields });
      toast.error(ae.message || "Save failed");
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!selId) return;
    if (!confirm("Delete this assignment?")) return;
    setBusy(true);
    try {
      await api.deleteBinAssignment(selId);
      setSelId("");
      setItems(await api.listBinAssignments());
      toast.success("Deleted");
    } catch (e: any) {
      toast.error((e as ApiError).message || "Delete failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card">
      <h2>Admin: Bin Assignments</h2>

      <div className="grid3">
        <label>
          Assignment
          <select
            value={selId}
            onChange={(e) => setSelId(e.target.value)}
            disabled={busy}
          >
            <option value="">-- select assignment --</option>
            {items.map((a) => {
              const c = contractors.find((x) => x.id === a.contractor_id);
              const label = c ? `${c.name} — ${a.zone_id || "-"}` : a.id;
              return (
                <option key={a.id} value={a.id}>
                  {label}
                </option>
              );
            })}
          </select>
        </label>

        <div className="row" style={{ alignItems: "end" }}>
          <button onClick={createItem} disabled={busy}>
            + Assignment
          </button>
        </div>
      </div>

      {edit && (
        <div style={{ marginTop: 12 }}>
          <h3 style={{ margin: "8px 0" }}>Edit Assignment</h3>
          <div className="grid3">
            <label>
              Contractor
              <select
                value={edit.contractor_id}
                onChange={(e) =>
                  setEdit({ ...edit!, contractor_id: e.target.value })
                }
              >
                <option value="">-- select --</option>
                {contractors.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
              {errs.contractor_id ? (
                <small style={{ color: "#f39" }}>{errs.contractor_id}</small>
              ) : null}
            </label>

            <label>
              Zone / Site ID
              <input
                value={edit.zone_id ?? ""}
                onChange={(e) => setEdit({ ...edit!, zone_id: e.target.value })}
                placeholder="e.g. SITE1 / ZONE_A"
              />
            </label>

            <label>
              Bin Size
              <input
                value={edit.bin_size ?? ""}
                onChange={(e) => setEdit({ ...edit!, bin_size: e.target.value })}
                placeholder="e.g. 6m3 / 240L"
              />
            </label>
          </div>

          <div className="grid3" style={{ marginTop: 8 }}>
            <label>
              Color
              <input
                value={edit.color ?? ""}
                onChange={(e) => setEdit({ ...edit!, color: e.target.value })}
                placeholder="e.g. green"
              />
            </label>
            <label>
              Notes
              <input
                value={edit.notes ?? ""}
                onChange={(e) => setEdit({ ...edit!, notes: e.target.value })}
              />
            </label>
            <label className="row" style={{ gap: 8, alignItems: "center" }}>
              <input
                type="checkbox"
                checked={Boolean(edit.active)}
                onChange={(e) => setEdit({ ...edit!, active: e.target.checked })}
              />
              Active
            </label>
          </div>

          <div className="row" style={{ marginTop: 8 }}>
            <button onClick={save} disabled={busy}>
              Save
            </button>
            <button className="ghost" onClick={remove} disabled={busy}>
              Delete
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
