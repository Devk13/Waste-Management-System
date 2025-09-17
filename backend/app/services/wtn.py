# ======================================================================
# file: backend/app/services/wtn.py
# Safe: no unresolved imports; PDF engine auto-detect.
# ======================================================================
from __future__ import annotations

import os
import json
import shutil
import subprocess
import tempfile
import importlib
from datetime import datetime
from typing import Any, Dict

WTN_FORM_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Waste Transfer Note {{ part1.wtn_number or part1.wtn_id }}</title>
  <style>
    @page { size: A4; margin: 16mm; }
    body { font-family: Arial, sans-serif; font-size: 12px; color: #111; }
    .grid { width: 100%; border: 2px solid #000; border-collapse: collapse; }
    .row { border-top: 1px solid #000; }
    .hdr { font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }
    .lcol { width: 36px; writing-mode: vertical-rl; transform: rotate(180deg);
            text-align: center; font-weight: bold; border-right: 1px solid #000; }
    .box { padding: 10px; }
    .p1 { background: #f3f3f3; }
    .p2 { background: #fde9df; }
    .p3 { background: #e9f3e9; }
    .field { margin: 6px 0; }
    .label { font-weight: bold; }
    .underline { display: inline-block; min-width: 240px; border-bottom: 1px solid #000; }
    .two > div { display: inline-block; min-width: 48%; vertical-align: top; }
    table.meta { width: 100%; border-collapse: collapse; margin-top: 4px; }
    table.meta td { padding: 4px 0; vertical-align: top; }
  </style>
</head>
<body>
  <table class="grid">
    <tr class="row"><td class="lcol">P<br/>A<br/>R<br/>T<br/><br/>1</td>
      <td class="box p1">
        <div class="hdr">Waste Originator</div>
        <div class="field">I CONFIRM THAT <span class="underline">{{ part1.quantity }}</span> (QUANTITY) OF <span class="underline">{{ part1.waste_type }}</span> TYPE OF WASTE WAS</div>
        <div class="two">
          <div class="field">LOADED ON <span class="underline">{{ part1.date_time }}</span> (DATE &amp; TIME)</div>
          <div class="field">FROM <span class="underline">{{ part1.originator_location }}</span> (ORIGINATOR LOCATION)</div>
        </div>
        <div class="field">AND WILL BE TRANSPORTED TO <span class="underline">{{ part1.destination_location }}</span> AS APPROVED LOCATION.</div>
        <table class="meta">
          <tr><td class="label">NAME:</td><td><span class="underline">{{ part1.name }}</span></td>
              <td class="label">ID NO.:</td><td><span class="underline">{{ part1.id_no }}</span></td>
              <td class="label">SIGNATURE:</td><td><span class="underline">{{ part1.signature }}</span></td></tr>
          <tr><td class="label">TEL NO.:</td><td colspan="5"><span class="underline">{{ part1.tel_no }}</span></td></tr>
        </table>
      </td>
    </tr>
    <tr class="row"><td class="lcol">P<br/>A<br/>R<br/>T<br/><br/>2</td>
      <td class="box p2">
        <div class="hdr">Waste Transporter</div>
        <div class="field">I SHALL TRANSPORT THE AFOREMENTIONED WASTE TO <span class="underline">{{ part2.to_location }}</span> (Location).</div>
        <table class="meta">
          <tr><td class="label">COMPANY NAME:</td><td colspan="5"><span class="underline">{{ part2.company_name }}</span></td></tr>
          <tr><td class="label">NAME:</td><td><span class="underline">{{ part2.name }}</span></td>
              <td class="label">ID / IQAMA NO.:</td><td><span class="underline">{{ part2.id_no }}</span></td>
              <td class="label">SIGNATURE:</td><td><span class="underline">{{ part2.signature }}</span></td></tr>
          <tr><td class="label">TEL NO.:</td><td><span class="underline">{{ part2.tel_no }}</span></td>
              <td class="label">PLATE NO.:</td><td colspan="3"><span class="underline">{{ part2.plate_no }}</span></td></tr>
        </table>
      </td>
    </tr>
    <tr class="row"><td class="lcol">P<br/>A<br/>R<br/>T<br/><br/>3</td>
      <td class="box p3">
        <div class="hdr">Waste Receiver</div>
        <div class="two">
          <div class="field">I CONFIRM RECEIPT OF THE STATED WASTE <span class="underline">{{ part3.quantity }}</span> (QUANTITY)</div>
          <div class="field">ON <span class="underline">{{ part3.date_time }}</span> (DATE &amp; TIME)</div>
        </div>
        <div class="field">AT ABOVE LOCATION AND WILL DISPOSE OF/TREAT THE WASTE AS APPROVED. DISPOSAL/TREATMENT IS <span class="underline">{{ part3.treatment }}</span></div>
        <table class="meta">
          <tr><td class="label">NAME:</td><td><span class="underline">{{ part3.name }}</span></td>
              <td class="label">ID/IQAMA NO.:</td><td><span class="underline">{{ part3.id_no }}</span></td>
              <td class="label">SIGNATURE OF RECEIVER &amp; STAMP:</td><td><span class="underline">{{ part3.signature }}</span></td></tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

def _ctx_get(section: dict, key: str, default: str = "") -> str:
    return str(section.get(key, default) or "")

def build_ctx_form(payload: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    p1 = payload.get("part1", {}) or {}
    p2 = payload.get("part2", {}) or {}
    p3 = payload.get("part3", {}) or {}
    return {
        "part1": {
            "wtn_number": payload.get("wtn_number"),
            "wtn_id": payload.get("wtn_id"),
            "quantity": _ctx_get(p1, "quantity"),
            "waste_type": _ctx_get(p1, "waste_type"),
            "date_time": _ctx_get(p1, "date_time", now),
            "originator_location": _ctx_get(p1, "originator_location"),
            "destination_location": _ctx_get(p1, "destination_location"),
            "name": _ctx_get(p1, "name"),
            "id_no": _ctx_get(p1, "id_no"),
            "signature": _ctx_get(p1, "signature"),
            "tel_no": _ctx_get(p1, "tel_no"),
        },
        "part2": {
            "to_location": _ctx_get(p2, "to_location"),
            "company_name": _ctx_get(p2, "company_name"),
            "name": _ctx_get(p2, "name"),
            "id_no": _ctx_get(p2, "id_no"),
            "signature": _ctx_get(p2, "signature"),
            "tel_no": _ctx_get(p2, "tel_no"),
            "plate_no": _ctx_get(p2, "plate_no"),
        },
        "part3": {
            "quantity": _ctx_get(p3, "quantity") or _ctx_get(p1, "quantity"),
            "date_time": _ctx_get(p3, "date_time", now),
            "treatment": _ctx_get(p3, "treatment"),
            "name": _ctx_get(p3, "name"),
            "id_no": _ctx_get(p3, "id_no"),
            "signature": _ctx_get(p3, "signature"),
        },
    }

def render_wtn_html(ctx: Dict[str, Any]) -> str:
    try:
        from jinja2 import Environment, BaseLoader  # optional, small
        return Environment(loader=BaseLoader(), autoescape=True).from_string(WTN_FORM_HTML).render(**ctx)
    except Exception:
        return "<html><body><pre>Install jinja2 to render WTN.</pre></body></html>"

def _weasyprint_available() -> bool:
    try:
        importlib.import_module("weasyprint")
        return True
    except Exception:
        return False

def _wkhtmltopdf_path() -> str | None:
    return shutil.which("wkhtmltopdf")

def render_wtn_pdf(html: str) -> bytes:
    # Prefer WeasyPrint (Python lib), then wkhtmltopdf (CLI)
    if _weasyprint_available():
        mod = importlib.import_module("weasyprint")
        # Avoid unresolved-import warning by not importing at module top.
        return mod.HTML(string=html).write_pdf()

    wk = _wkhtmltopdf_path()
    if wk:
        with tempfile.TemporaryDirectory() as td:
            inp, out = os.path.join(td, "wtn.html"), os.path.join(td, "wtn.pdf")
            with open(inp, "w", encoding="utf-8") as f:
                f.write(html)
            proc = subprocess.run([wk, "--quiet", inp, out], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode != 0 or not os.path.exists(out):
                raise RuntimeError(proc.stderr.decode(errors="ignore"))
            with open(out, "rb") as f:
                return f.read()

    raise RuntimeError("No PDF engine available; install 'weasyprint' or provide 'wkhtmltopdf'.")
