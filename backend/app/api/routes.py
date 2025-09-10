# app/api/routes.py
from fastapi import APIRouter

router = APIRouter()

def _try_include(modname: str) -> None:
    try:
        mod = __import__(f"app.api.{modname}", fromlist=["router"])
        r = getattr(mod, "router", None)
        if r is None:
            print(f"[routes] {modname}: no 'router' attr, skipping")
            return
        router.include_router(r)
        print(f"[routes] mounted '{modname}'")
    except Exception as e:
        # Don't crash the whole app just because this module isn't ready.
        print(f"[routes] skipping '{modname}': {e}")

# Always try to mount /skips (you already have this working)
_try_include("skips")

# Optional modules — only mount if they import cleanly
for name in ("driver", "dispatch", "drivers"):  # 'drivers' is your /drivers/me file
    _try_include(name)
