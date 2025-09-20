// ===========================
// frontend/src/components/ContractorsAdmin.tsx
// ===========================
import React, { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "../api";
import { toast } from "../ui/toast";

type ContractorsAdminProps = {
  onResult?: (title: string, payload: any) => void;
};

type Contractor = {
  id: string;
  org_name: string;
  contact_name?: string;
  phone?: string;
  email?: string;
  active?: boolean;
};

export default function ContractorsAdmin({ onResult }: ContractorsAdminProps) {
  const [items, setItems] = useState<Contractor[]>([]);
  const [selId, setSelId] = useState<string>("");
  const [edit, setEdit] = useState<Contractor | null>(null);
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);

  const selected = useMemo(
    () => items.find((x) => x.id === selId) ?? null,
    [items, selId]
  );

  useEffect(() => {
    (async () => {
      try {
        setItems(await api.listContractors());
      } catch (e: any) {
        toast.error("Failed to load contractors", e?.message);
      }
    })();
  }, []);

  useEffect(() => {
    if (selected) {
      setEdit({
        id: selected.id,
        org_name: selected.org_name ?? "",
        contact_name: selected.contact_name ?? "",
        phone: selected.phone ?? "",
        email: selected.email ?? "",
        active: Boolean(selected.active ?? true),
      });
    } else {
      setEdit(null);
    }
    setErrs({});
  }, [selected]);

  const validate = (p: Partial<Contractor>) => {
    const e: Record<string, string> = {};
    if (!p.org_name?.trim()) e.name = "Name is required";
    if ((p.org_name || "").length > 120) e.name = "Name too long";
    if (p.email && !/^\S+@\S+\.\S+$/.test(p.email)) e.email = "Invalid email";
    return e;
  };

  const createItem = async () => {
  const name = prompt("Contractor name", "ACME Contracting");
  if (!name) return;
  setBusy(true);
  try {
    const res = await api.createContractor({ org_name: name });
    setItems(await api.listContractors());
    onResult?.("Create contractor", res);
    toast.success("Contractor created");
  } catch (e) {
    const ae = e as ApiError;
    toast.error(ae.message || "Create failed");
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
      const res = await api.updateContractor(selId, {
        org_name: edit.org_name,
        contact_name: edit.contact_name ?? "",
        phone: edit.phone ?? "",
        email: edit.email ?? "",
        active: Boolean(edit.active),
      });
      onResult?.("Update contractor", res);
      setItems(await api.listContractors());
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
    if (!confirm("Delete this contractor?")) return;
    setBusy(true);
    try {
      await api.deleteContractor(selId);
      setSelId("");
      setItems(await api.listContractors());
      toast.success("Deleted");
    } catch (e: any) {
      toast.error((e as ApiError).message || "Delete failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card">
      <h2>Admin: Contractors</h2>
      <div className="grid3">
        <label>
            Contractor
            <select
                value={selId}
                onChange={(e) => setSelId(e.target.value)}
                disabled={busy}
            >
                <option value="">-- select contractor --</option>
                {items.map((c) => (
                <option key={c.id} value={c.id}>{c.org_name}</option>
                ))}
            </select>
        </label>
        <div className="row" style={{ alignItems: "end" }}>
          <button onClick={createItem} disabled={busy}>
            + Contractor
          </button>
        </div>
      </div>
      {edit && (
        <div style={{ marginTop: 12 }}>
          <h3 style={{ margin: "8px 0" }}>Edit Contractor</h3>
          <div className="grid3">
            <label>
              Name
              <input
                value={edit.org_name}
                onChange={(e) => {
                  setEdit({ ...edit!, org_name: e.target.value });
                  setErrs({ ...errs, name: "" });
                }}
              />
              {errs.name ? <small style={{ color: "#f39" }}>{errs.name}</small> : null}
            </label>
            <label>
              Contact
              <input
                value={edit.contact_name ?? ""}
                onChange={(e) => setEdit({ ...edit!, contact_name: e.target.value })}
              />
            </label>
            <label>
              Phone
              <input
                value={edit.phone ?? ""}
                onChange={(e) => setEdit({ ...edit!, phone: e.target.value })}
              />
            </label>
          </div>
          <div className="grid3" style={{ marginTop: 8 }}>
            <label>
              Email
              <input
                value={edit.email ?? ""}
                onChange={(e) => {
                  setEdit({ ...edit!, email: e.target.value });
                  setErrs({ ...errs, email: "" });
                }}
              />
              {errs.email ? (
                <small style={{ color: "#f39" }}>{errs.email}</small>
              ) : null}
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
