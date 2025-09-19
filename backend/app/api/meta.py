# path: backend/app/api/meta.py

from __future__ import annotations

import os, time, subprocess
from typing import Any, Dict
from fastapi import APIRouter

from app.core.config import (
    get_skip_color_legend,
    get_skip_size_presets,
)

router = APIRouter(tags=["__meta"])

def _colors_payload() -> Dict[str, Dict[str, Any]]:
    """
    Shape colors with a friendly label so the UI can render 'key — label'.
    """
    legend = get_skip_color_legend()
    out: Dict[str, Dict[str, Any]] = {}
    for key, spec in legend.items():
        label = spec.get("waste") or spec.get("notes") or key
        out[key] = {
            "label": label,
            **spec,  # include raw fields: waste, sizes_m3, wheelie_l, rolloff_yd, notes
        }
    return out

def _sizes_payload() -> Dict[str, Any]:
    return get_skip_size_presets()

def _meta_payload() -> Dict[str, Any]:
    return {
        "skip": {
            "colors": _colors_payload(),
            "sizes": _sizes_payload(),
        }
    }

def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception:
        return os.getenv("GIT_SHA", "unknown")

def _payload():
    from app.core.config import settings  # avoid circulars
    return {
        "backend": {
            "sha": _git_sha(),
            "built_at": os.getenv("BUILD_AT", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
            "env": getattr(settings, "ENV", "dev"),
        }
    }

@router.get("/meta/config")
async def meta_config() -> Dict[str, Any]:
    return _meta_payload()

# Also expose under /_meta for convenience/allow-list compatibility
@router.get("/_meta/config")
async def meta_config_underscore() -> Dict[str, Any]:
    return _meta_payload()

@router.get("/meta/versions")
async def meta_versions(): return _payload()

@router.get("/_meta/versions")
async def meta_versions_underscore(): return _payload()
