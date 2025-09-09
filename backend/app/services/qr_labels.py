# path: backend/app/services/qr_labels.py
from __future__ import annotations

from io import BytesIO
from dataclasses import dataclass
from typing import Optional

import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader


@dataclass
class LabelMeta:
    qr_text: str          # full deeplink or raw code
    qr_code: str          # human readable code (e.g., SK-1A2B3C4D)
    org_name: str         # printed on label
    subtitle: Optional[str] = None


def make_qr_png(data: str, box_size: int = 8, border: int = 2) -> bytes:
    """
    Returns PNG bytes for a QR code.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_three_up_pdf(meta: LabelMeta, qr_png: bytes) -> bytes:
    """
    3-up label sheet (A4). Each label shows QR + org + code.
    """
    page_w, page_h = A4
    label_w, label_h = 90 * mm, 40 * mm
    gap = 12 * mm

    total_h = 3 * label_h + 2 * gap
    start_y = (page_h - total_h) / 2
    x = (page_w - label_w) / 2

    qr_img = ImageReader(BytesIO(qr_png))

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    for i in range(3):
        y = start_y + (2 - i) * (label_h + gap)

        # frame
        c.roundRect(x, y, label_w, label_h, 6 * mm, stroke=1, fill=0)

        # qr
        qr_size = 32 * mm
        c.drawImage(
            qr_img,
            x + 6 * mm,
            y + (label_h - qr_size) / 2,
            qr_size,
            qr_size,
            preserveAspectRatio=True,
            mask="auto",
        )

        # text block
        tx = x + 6 * mm + qr_size + 6 * mm
        ty = y + label_h - 10 * mm

        c.setFont("Helvetica-Bold", 10)
        c.drawString(tx, ty, meta.org_name[:40])

        c.setFont("Helvetica-Bold", 12)
        c.drawString(tx, ty - 6 * mm, f"SKIP {meta.qr_code}")

        c.setFont("Helvetica", 8)
        if meta.subtitle:
            c.drawString(tx, ty - 12 * mm, meta.subtitle[:48])

        c.setFont("Helvetica", 7)
        c.setFillGray(0.3)
        c.drawString(tx, y + 6 * mm, meta.qr_text[:80])
        c.setFillGray(0)

    c.showPage()
    c.save()
    return buf.getvalue()
