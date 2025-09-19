from __future__ import annotations

import argparse
import json
from urllib import request as _r, error as _e


def _call(method: str, url: str, headers: dict | None = None, body: bytes | None = None):
    req = _r.Request(url, method=method, headers=headers or {}, data=body)
    try:
        with _r.urlopen(req, timeout=10) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "ignore")
    except _e.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "ignore")
    except Exception as e:
        return f"ERR:{e}", {}, ""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://127.0.0.1:8000")
    p.add_argument("--key", default="driverapi")
    args = p.parse_args()

    base = args.base.rstrip("/")
    url = f"{base}/driver/dev/ensure-skip"

    print("1) OPTIONS preflight (expect 204)…")
    s, h, b = _call("OPTIONS", url, {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "x-api-key,content-type",
    })
    print("   status:", s, "allow-origin:", h.get("access-control-allow-origin"))

    print("2) GET no key (expect 401)…")
    s, _, b = _call("GET", url)
    print("   status:", s, "body:", b)

    print("3) GET with x-api-key (expect 200)…")
    s, _, b = _call("GET", url, {"x-api-key": args.key})
    print("   status:", s, "body:", b)

    print("4) GET with Bearer (expect 200)…")
    s, _, b = _call("GET", url, {"Authorization": f"Bearer {args.key}"})
    print("   status:", s, "body:", b)

    print("5) Routes probe (open)…")
    s, _, b = _call("GET", f"{base}/_debug/routes")
    print("   status:", s, "has /driver?:", "/driver" in b)


if __name__ == "__main__":
    main()
