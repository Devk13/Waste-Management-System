# path: backend/app/core/config.py
from __future__ import annotations

from typing import TypedDict, Dict, List
import os
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── helpers ──────────────────────────────────────────────────────────────────

def _normalize_db_url(raw: str | None) -> str:
    """
    Convert common URLs to async drivers:
      postgres://…?sslmode=require  -> postgresql+asyncpg://…?ssl=true
      postgresql://…                -> postgresql+asyncpg://…
      sqlite://…                    -> sqlite+aiosqlite://…
    """
    if not raw:
        return ""
    # Accept SQLAlchemy URL objects too
    s = raw if isinstance(raw, str) else str(raw)
    s = s.strip()
    if not s:
        return ""

    # sqlite -> aiosqlite
    if s.startswith("sqlite://") and "+aiosqlite" not in s:
        s = s.replace("sqlite://", "sqlite+aiosqlite://", 1)

    from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
    u = urlparse(s)
    scheme = u.scheme
    if scheme.startswith("postgres"):
        scheme = "postgresql+asyncpg"

    q = dict(parse_qsl(u.query, keep_blank_values=True))
    if "sslmode" in q:  # Render often sets sslmode=require
        q.pop("sslmode", None)
        q.setdefault("ssl", "true")
    elif scheme.startswith("postgresql"):
        q.setdefault("ssl", "true")

    return urlunparse(u._replace(scheme=scheme, query=urlencode(q)))


def _split_sc(v: str | None) -> list[str]:
    """Split by ';' or ','; trim; return ['*'] if wildcard/empty."""
    if not v or v.strip() == "*":
        return ["*"]
    return [x.strip() for x in v.replace(",", ";").split(";") if x.strip()]


def _parse_color_map(spec: str | None) -> dict[str, str]:
    """Parse 'yellow=general;red=hazardous' (semicolon-delimited)."""
    if not spec:
        return {}
    out: dict[str, str] = {}
    for part in spec.split(";"):
        k, _, v = part.partition("=")
        k, v = k.strip(), v.strip()
        if k and v:
            out[k] = v
    return out


def _bool(v: str | bool | None, default: bool = False) -> bool:
    """Env-friendly bool; ensures predictable behavior."""
    if isinstance(v, bool):
        return v
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "on"}


# ── Skip / container canonical constants ─────────────────────────────────────

class ColorSpec(TypedDict, total=False):
    waste: str
    sizes_m3: List[int]
    wheelie_l: List[int]
    rolloff_yd: List[int]
    notes: str

SKIP_SIZES_M3: List[int]  = [6, 8, 12]
WHEELIE_LITRES: List[int] = [120, 240, 660, 1100]
ROLLOFF_YARDS: List[int]  = [20, 30]

# keys lower-case for simple lookups
SKIP_COLOR_SPEC: Dict[str, ColorSpec] = {
    "white":  {"waste": "Gypsum & plasterboard", "sizes_m3": SKIP_SIZES_M3, "wheelie_l": WHEELIE_LITRES},
    "grey":   {"waste": "Inert (concrete/brick/rubble)", "sizes_m3": SKIP_SIZES_M3, "rolloff_yd": ROLLOFF_YARDS},
    "black":  {"waste": "Mixed general (non-recyclable)", "sizes_m3": SKIP_SIZES_M3, "wheelie_l": [240, 660, 1100]},
    "blue":   {"waste": "Clean metal (scrap, rebar offcuts)", "sizes_m3": SKIP_SIZES_M3, "wheelie_l": [240, 660]},
    "green":  {"waste": "Clean untreated wood/timber", "sizes_m3": SKIP_SIZES_M3, "wheelie_l": [240, 660, 1100]},
    "brown":  {"waste": "Packaging (cardboard, paper)", "wheelie_l": WHEELIE_LITRES, "notes": "Prefer baler bins where available."},
    "orange": {"waste": "Hazardous (asbestos/chemicals)", "wheelie_l": [240, 660], "notes": "Secure-lid wheelies; sealed skips/drums."},
}

def get_skip_color_legend() -> Dict[str, ColorSpec]:
    return SKIP_COLOR_SPEC

def get_skip_size_presets() -> Dict[str, List[int]]:
    return {"sizes_m3": SKIP_SIZES_M3, "wheelie_l": WHEELIE_LITRES, "rolloff_yd": ROLLOFF_YARDS}


# ── settings ────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    # env/runtime
    ENV: str = "dev"
    DEBUG: bool = False
    EXPOSE_ADMIN_ROUTES: bool = False

    # auth
    DRIVER_API_KEY: str = "driverapi"
    ADMIN_API_KEY: str = "super-temp-seed-key"
    JWT_SECRET: str = "dev"

    # DB
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"

    # CORS / frontend base
    # Prefer explicit origins in prod (comma/semicolon separated).
    CORS_ORIGINS: str = "*"
    # Optional alias; if set, appended to CORS_ORIGINS for convenience.
    FRONTEND_ORIGINS: str = ""
    CORS_ALLOW_CREDENTIALS: bool = True
    DRIVER_QR_BASE_URL: str = "http://localhost:5173"  # ⚠ dev default; use https in prod

    # Feature flags
    ENABLE_DRIVER_JOBS_SCHEDULE: bool = False  # gate for /driver/schedule if needed

    # Skip options (env-overridable convenience)
    SKIP_SIZES: str = "2yd;4yd;6yd;8yd;12yd"
    SKIP_COLOR_MEANINGS: str = "yellow=general;red=hazardous;blue=recycling"

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local", ".env.production"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

# Instantiate once
settings = Settings()

# Normalize DATABASE_URL using merged env (not os.getenv).
settings.DATABASE_URL = _normalize_db_url(settings.DATABASE_URL)

# Build CORS origins list from both envs
_origins = []
_origins.extend(_split_sc(settings.CORS_ORIGINS))
if settings.FRONTEND_ORIGINS.strip():
    _origins.extend([o for o in _split_sc(settings.FRONTEND_ORIGINS) if o not in {"*", ""}])

# Deduplicate while preserving order
seen = set()
CORS_ORIGINS_LIST: list[str] = []
for o in _origins:
    if o not in seen:
        seen.add(o)
        CORS_ORIGINS_LIST.append(o)

# If wildcard is present or list ends up ["*"], credentials must be off.
WILDCARD = (CORS_ORIGINS_LIST == ["*"]) or ("*" in CORS_ORIGINS_LIST)
CORS_ALLOW_CREDENTIALS_EFFECTIVE: bool = False if WILDCARD else _bool(settings.CORS_ALLOW_CREDENTIALS, default=False)

# Public exports for skip meta
SKIP_SIZES_LIST: list[str] = _split_sc(settings.SKIP_SIZES)
SKIP_COLOR_MAP: dict[str, str] = _parse_color_map(settings.SKIP_COLOR_MEANINGS)

# Convenience kwargs for CORSMiddleware to avoid misconfiguration.
# Why: browsers reject '*' with credentials; centralize the rule.
CORS_KWARGS = {
    "allow_origins": ["*"] if WILDCARD else CORS_ORIGINS_LIST,
    "allow_credentials": CORS_ALLOW_CREDENTIALS_EFFECTIVE,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

# Optional: quick summary for debug endpoints
SETTINGS_SUMMARY = {
    "env": settings.ENV,
    "debug": settings.DEBUG,
    "expose_admin_routes": settings.EXPOSE_ADMIN_ROUTES,
    "db_url_driver": settings.DATABASE_URL.split("://", 1)[0],
    "cors_origins": CORS_ORIGINS_LIST,
    "cors_allow_credentials": CORS_ALLOW_CREDENTIALS_EFFECTIVE,
    "wildcard": WILDCARD,
    "enable_driver_jobs_schedule": settings.ENABLE_DRIVER_JOBS_SCHEDULE,
}

ADMIN_API_KEY: str = settings.ADMIN_API_KEY
DRIVER_API_KEY: str = settings.DRIVER_API_KEY
DATABASE_URL: str = settings.DATABASE_URL
EXPOSE_ADMIN_ROUTES: bool = settings.EXPOSE_ADMIN_ROUTES
