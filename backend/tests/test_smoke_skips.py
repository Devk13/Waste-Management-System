import os
from fastapi.testclient import TestClient

os.environ.setdefault("ENV", "dev")
from app.main import app  # noqa: E402

client = TestClient(app)

def test_debug_routes_lists_skips_prefix():
    r = client.get("/__debug/routes")
    assert r.status_code == 200
    assert any(item["path"].startswith("/skips") for item in r.json())

def test_skips_smoke_ok():
    r = client.get("/skips/__smoke")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert "ts" in data

