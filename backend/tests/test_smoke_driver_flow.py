# path: backend/tests/test_smoke_driver_flow.py
from __future__ import annotations
import os
import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from app.main import app

# make sure we boot in dev for tests
os.environ.setdefault("ENV", "dev")
os.environ.setdefault("DRIVER_API_KEY", "driverapi")
os.environ.setdefault("ADMIN_API_KEY", "super-temp-seed-key")

DKEY = os.environ["DRIVER_API_KEY"]
AKEY = os.environ["ADMIN_API_KEY"]
H_D  = {"X-API-Key": DKEY}
H_A  = {"X-API-Key": AKEY}

def _msg(step: str, r) -> str:
    return f"{step}: {r.status_code} -> {r.text}"

@pytest.mark.asyncio
async def test_driver_flow_and_wtn_html_ok():
    transport = ASGITransport(app=app)
    async with LifespanManager(app):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Probe routes first (helps explain 404s)
            r = await ac.get("/_meta/ping")
            assert r.status_code == 200, _msg("_meta/ping", r)

            routes = await ac.get("/_debug/routes", headers=H_A)  # admin key not required in dev, fine if present
            assert routes.status_code == 200, _msg("_debug/routes", routes)
            route_paths = {p["path"] for p in routes.json()}
            print("ROUTES:", sorted(list(route_paths))[:25], "...")

            qr = "QR-SMOKE-001"

            # -------- seed skip (try /driver/dev/ensure-skip, then /skips/_seed) ----------
            seeded = False
            if "/driver/dev/ensure-skip" in route_paths:
                r = await ac.post("/driver/dev/ensure-skip", headers=H_D, json={"qr_code": qr, "qr": qr})
                if r.status_code == 422:
                    r = await ac.get(f"/driver/dev/ensure-skip?qr={qr}", headers=H_D)
                assert r.status_code in (200, 201), _msg("dev/ensure-skip", r)
                seeded = True
            elif "/skips/_seed" in route_paths:
                r = await ac.post("/skips/_seed", headers=H_A, json={"qr": qr, "color": "green", "size": "6m3"})
                assert r.status_code in (200, 201), _msg("skips/_seed", r)
                seeded = True

            assert seeded, f"No seed endpoint found (routes has {sorted(list(route_paths))[:20]} ...)."

            # -------- scan ----------
            r = await ac.get(f"/driver/scan?qr={qr}", headers=H_D)
            assert r.status_code == 200, _msg("driver/scan", r)

            # -------- deliver ----------
            r = await ac.post("/driver/deliver-empty", headers=H_D, json={
                "skip_qr": qr, "to_zone_id": "ZONE_C", "driver_name": "Test Driver", "vehicle_reg": "TEST-001"
            })
            assert r.status_code == 201, _msg("driver/deliver-empty", r)

            # -------- relocate ----------
            r = await ac.post("/driver/relocate-empty", headers=H_D, json={
                "skip_qr": qr, "to_zone_id": "ZONE_B", "driver_name": "Test Driver"
            })
            assert r.status_code == 201, _msg("driver/relocate-empty", r)

            # -------- collect (creates WTN) ----------
            r = await ac.post("/driver/collect-full", headers=H_D, json={
                "skip_qr": qr,
                "destination_type": "RECYCLING",
                "destination_name": "ECO MRF",
                "weight_source": "WEIGHBRIDGE",
                "gross_kg": 2500, "tare_kg": 1500,
                "driver_name": "Test Driver", "site_id": "SITE1", "vehicle_reg": "TEST-001"
            })
            assert r.status_code == 201, _msg("driver/collect-full", r)
            wtn_url = r.json().get("wtn_pdf_url")
            assert isinstance(wtn_url, str) and wtn_url.endswith(".pdf"), "collect-full missing wtn_pdf_url"

            # -------- return ----------
            r = await ac.post("/driver/return-empty", headers=H_D, json={
                "skip_qr": qr, "to_zone_id": "ZONE_C", "driver_name": "Test Driver"
            })
            assert r.status_code in (200, 201), _msg("driver/return-empty", r)

            # -------- WTN HTML reachable ----------
            r = await ac.get(f"{wtn_url}?format=html")
            assert r.status_code == 200, _msg("GET WTN HTML", r)

            # -------- list recent WTN (debug) ----------
            if "/__debug/wtns" in route_paths:
                r = await ac.get("/__debug/wtns?limit=1", headers=H_A)
                assert r.status_code == 200, _msg("__debug/wtns", r)
