# ======================================================================
# file: backend/app/models/__init__.py
# ======================================================================
from __future__ import annotations

# Re-export Base so "from app.models import Base" works everywhere
from .base import Base  # noqa: F401

# Import modules for mapper registration side-effects
from . import skip as _skip_models   # noqa: F401
from . import labels as _label_models  # noqa: F401
try:
    from . import models as _core_models  # contains SkipPlacement in some repos
except Exception:
    _core_models = None  # noqa: F841

# Re-export common ORM classes from their *actual* modules
from .skip import Skip, SkipStatus  # noqa: F401
from .labels import SkipAsset, SkipAssetKind  # noqa: F401

# SkipPlacement is defined in either skip.py or models.py depending on branch
try:
    from .skip import SkipPlacement  # type: ignore  # noqa: F401
except Exception:
    try:
        from .models import SkipPlacement  # type: ignore  # noqa: F401
    except Exception:
        # As a last resort, leave it undefined so a wrong import fails loudly
        pass

__all__ = [
    "Base",
    "Skip", "SkipStatus",
    "SkipAsset", "SkipAssetKind",
    "SkipPlacement",  # if available
]
