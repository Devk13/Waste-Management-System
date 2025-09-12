# path: backend/app/core/config.py
from __future__ import annotations
# extra typing for the color/spec maps
from typing import TypedDict, Dict, List
import os
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from pydantic_settings import BaseSettings, SettingsConfigDict


# --- helpers ---------------------------------------------------------------

def _split(v: str | None) -> list[str]:
    """Split on ; or , and trim; return ['*'] if empty or '*'."""
    if not v or v.strip() == "*":
        return ["*"]
    return [x.strip() for x in v.replace(",", ";").split(";") if x.strip()]


def _normalize_db_url(raw: str) -> str:
    """
    Accepts Render-style postgres URLs like:
      postgres://user:pass@host:5432/db?sslmode=require
    …and converts to asyncpg form:
      postgresql+asyncpg://user:pass@host:5432/db?ssl=true
    """
    if not raw:
        return raw

    u = urlparse(raw)

    # 1) scheme -> asyncpg
    scheme = u.scheme
    if scheme.startswith("postgres"):
        scheme = "postgresql+asyncpg"

    # 2) query params
    q = dict(parse_qsl(u.query, keep_blank_values=True))
    # Render sets sslmode=require; asyncpg wants ssl=true
    if "sslmode" in q:
        q.pop("sslmode", None)
        q.setdefault("ssl", "true")
    else:
        # enforce ssl on managed DBs by default
        q.setdefault("ssl", "true")

    new = u._replace(scheme=scheme, query=urlencode(q))
    return urlunparse(new)

# ─────────────────────────────────────────────────────────────────────────────
# Skip / container canonical constants (Saudi color code + sizes)
# ─────────────────────────────────────────────────────────────────────────────

class ColorSpec(TypedDict, total=False):
    waste: str
    # Supported container families for the color
    sizes_m3: List[int]         # standard skip sizes
    wheelie_l: List[int]        # wheelie bin capacities (litres)
    rolloff_yd: List[int]       # roll-off capacities (yards)
    notes: str                  # any guidance / restrictions

# Canonical size lists we’ll reuse across colors
SKIP_SIZES_M3: List[int]   = [6, 8, 12]
WHEELIE_LITRES: List[int]  = [120, 240, 660, 1100]
ROLLOFF_YARDS: List[int]   = [20, 30]

# Saudi construction waste color code (source you provided)
# Keys are lower-case to keep lookups simple.
SKIP_COLOR_SPEC: Dict[str, ColorSpec] = {
    "white": {
        "waste": "Gypsum & plasterboard",
        "wheelie_l": WHEELIE_LITRES,
        "sizes_m3": SKIP_SIZES_M3,
    },
    "grey": {
        "waste": "Inert (clean concrete, brick, block, rubble)",
        "sizes_m3": SKIP_SIZES_M3,
        "rolloff_yd": ROLLOFF_YARDS,
    },
    "black": {
        "waste": "Mixed general (non-recyclable)",
        "wheelie_l": [240, 660, 1100],
        "sizes_m3": SKIP_SIZES_M3,
    },
    "blue": {
        "waste": "Clean metal (scrap, rebar offcuts)",
        "wheelie_l": [240, 660],
        "sizes_m3": SKIP_SIZES_M3,
    },
    "green": {
        "waste": "Clean untreated wood/timber",
        "wheelie_l": [240, 660, 1100],
        "sizes_m3": SKIP_SIZES_M3,
    },
    "brown": {
        "waste": "Packaging (cardboard, paper)",
        "wheelie_l": [120, 240, 660, 1100],
        "notes": "Baler bins where available.",
    },
    "orange": {
        "waste": "Hazardous (asbestos, chemicals, contaminated items)",
        "wheelie_l": [240, 660],
        "notes": "Use secure-lid wheelies; sealed hazardous skips/drums.",
    },
}

def get_skip_color_legend() -> Dict[str, ColorSpec]:
    """Public helper so endpoints/services can return this to clients."""
    return SKIP_COLOR_SPEC

def get_skip_size_presets() -> Dict[str, List[int]]:
    """Handy bundle of canonical sizes."""
    return {
        "sizes_m3": SKIP_SIZES_M3,
        "wheelie_l": WHEELIE_LITRES,
        "rolloff_yd": ROLLOFF_YARDS,
    }

# --- settings --------------------------------------------------------------

class Settings(BaseSettings):
    # runtime env
    ENV: str = "dev"
    DEBUG: bool = False

    # DB
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    DRIVER_QR_BASE_URL: str = "http://localhost:5173"                    #remove after test
    CORS_ORIGINS: str = "*"                                                 #remove after test
    # TEMP: one-time key to allow /skips/_seed during smoke tests       #remove after test
    ADMIN_API_KEY: str | None = None                                     #remove after test
    # security
    JWT_SECRET: str = "dev"

    # frontend / CORS
    # Accept either ";" or "," separated list, or "*" for any (dev)
    CORS_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True  # will be forced False if origins == ['*']

    # where QR codes/driver links should land (frontend base)
    DRIVER_QR_BASE_URL: str = "http://localhost:5173"

    # --- Skip options (for later endpoints/UI wiring) ----------------------
    # You asked to support size and colour semantics.
    # Example env values:
    #   SKIP_SIZES="2yd;4yd;6yd;8yd;12yd"
    #   SKIP_COLOR_MEANINGS="yellow=general;red=hazardous;blue=recycling"
    SKIP_SIZES: str = "2yd;4yd;6yd;8yd;12yd"
    SKIP_COLOR_MEANINGS: str = "yellow=general;red=hazardous;blue=recycling"

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local", ".env.production"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
# --- small helpers -------------------------------------------------
def _split(raw: str | None) -> list[str]:
    """Split a comma list like 'a, b , c' -> ['a','b','c']."""
    return [p.strip() for p in (raw or "").split(",") if p.strip()]

def _parse_color_map(raw: str | None) -> dict[str, str]:
    """
    Parse 'Black=mixed; Green=wood' (comma-separated with '=') into a dict.
    """
    out: dict[str, str] = {}
    for part in (raw or "").split(","):
        k, _, v = part.partition("=")
        if k and v:
            out[k.strip()] = v.strip()
    return out

# Normalize DATABASE_URL coming from env (Render gives postgres://…)
settings.DATABASE_URL = _normalize_db_url(os.getenv("DATABASE_URL", settings.DATABASE_URL))

# ----- helpers (above usage) -----
def _split(s: str | None) -> list[str]:
    if not s:
        return []
    return [p.strip() for p in s.split(";") if p.strip()]

def _parse_color_map(s: str | None) -> dict[str, str]:
    if not s:
        return {}
    out: dict[str, str] = {}
    for part in s.split(";"):
        k, _, v = part.partition("=")
        k, v = k.strip(), v.strip()
        if k and v:
            out[k] = v
    return out

# ----- build settings object -----
settings = Settings()
settings.DATABASE_URL = _normalize_db_url(
    os.getenv("DATABASE_URL", settings.DATABASE_URL)
)

# ----- handy parsed exports (module-level, not attributes on `settings`) -----
CORS_ORIGINS_LIST: list[str] = _split(settings.CORS_ORIGINS)
SKIP_SIZES_LIST: list[str] = _split(settings.SKIP_SIZES)
SKIP_COLOR_MAP: dict[str, str] = _parse_color_map(settings.SKIP_COLOR_MEANINGS)
