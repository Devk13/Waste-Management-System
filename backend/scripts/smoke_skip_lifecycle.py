from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

BASE = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
QR = os.getenv("QR", "QR123")
API_KEY = os.getenv("X_API_KEY")

# Demo data (aligns with your screenshot)
DRIVER_NAME = os.getenv("DRIVER_NAME", "Alex")
VEHICLE_REG = os.getenv("VEHICLE_REG", "TEST-001")
ZONE_A = os.getenv("ZONE_A", "ZONE_A")
ZONE_B = os.getenv("ZONE_B", "ZONE_B")
ZONE_C = os.getenv("ZONE_C", "ZONE_C")
SITE_ID = os.getenv("SITE_ID", "SITE1")
DEST_TYPE = os.getenv("DEST_TYPE", "RECYCLING")
DEST_NAME = os.getenv("DEST_NAME", "ECO MRF")
WEIGHT_SOURCE = os.getenv("WEIGHT_SOURCE", "WEIGHBRIDGE")
GROSS_KG = float(os.getenv("GROSS_KG", "2500"))
TARE_KG = float(os.getenv("TARE_KG", "1500"))


def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY  # prod-only middleware; harmless locally
    return h


def _get(path: str) -> Dict[str, Any]:
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, headers=_headers(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        raise RuntimeError(f"GET {url} -> {e.code} {body}") from None
    except Exception as e:
        raise RuntimeError(f"GET {url} failed: {e}") from None


def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{BASE}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=_headers(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        raise RuntimeError(f"POST {url} -> {e.code} {body}") from None
    except Exception as e:
        raise RuntimeError(f"POST {url} failed: {e}") from None


def _print(title: str, obj: Any) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def ensure_skip(qr: str) -> Optional[Dict[str, Any]]:
    """Try to seed a dev skip if scan fails; supports GET or POST helper."""
    # Why: different dev helpers; try both shapes so this works out-of-the-box.
    qs = urllib.parse.urlencode({"qr": qr})
    for path in (f"/driver/dev/ensure-skip?{qs}", "/driver/dev/ensure-skip"):
        try:
            if path.endswith("ensure-skip"):
                return _post(path, {"qr": qr})
            return _get(path)
        except Exception:
            continue
    return None


def main() -> int:
    print(f"BASE={BASE}  QR={QR}")

    # 1) scan (and seed if missing)
    try:
        scan = _get("/driver/scan?" + urllib.parse.urlencode({"q": QR}))
    except Exception:
        seeded = ensure_skip(QR)
        if not seeded:
            print("Failed to seed test skip; ensure /driver/dev/ensure-skip exists.", file=sys.stderr)
            return 2
        # tiny wait to let DB commit show up
        time.sleep(0.2)
        scan = _get("/driver/scan?" + urllib.parse.urlencode({"q": QR}))
    _print("scan", scan)

    # 2) deliver-empty → ZONE_A
    deliver = _post("/driver/deliver-empty", {
        "skip_qr": QR,
        "to_zone_id": ZONE_A,
        "driver_name": DRIVER_NAME,
        "vehicle_reg": VEHICLE_REG,
    })
    _print("deliver-empty", deliver)

    # 3) relocate-empty → ZONE_B
    relocate = _post("/driver/relocate-empty", {
        "skip_qr": QR,
        "to_zone_id": ZONE_B,
        "driver_name": DRIVER_NAME,
    })
    _print("relocate-empty", relocate)

    # 4) collect-full → facility w/ weights
    collect = _post("/driver/collect-full", {
        "skip_qr": QR,
        "destination_type": DEST_TYPE,
        "destination_name": DEST_NAME,
        "weight_source": WEIGHT_SOURCE,
        "gross_kg": GROSS_KG,
        "tare_kg": TARE_KG,
        "driver_name": DRIVER_NAME,
        "site_id": SITE_ID,
    })
    _print("collect-full", collect)

    # 5) return-empty → ZONE_C
    back = _post("/driver/return-empty", {
        "skip_qr": QR,
        "to_zone_id": ZONE_C,
        "driver_name": DRIVER_NAME,
    })
    _print("return-empty", back)

    print("\nOK: skip lifecycle smoke complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())