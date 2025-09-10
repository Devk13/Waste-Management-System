# ─────────────────────────────────────────────────────────────────────────────
# path: backend/app/models/__init__.py  (REPLACE to remove missing .user import)
# Avoid importing a non-existent user module. Keep only what you have.
# ─────────────────────────────────────────────────────────────────────────────
from .skip import Base as SkipBase, Skip, SkipAsset, SkipStatus
# keep any other exports you already have here
from .labels import SkipAsset, SkipAssetKind
from .driver import DriverProfile, DriverAssignment  # noqa: F401

__all__ = ["Skip", "SkipStatus", "SkipAsset", "SkipAssetKind"]
