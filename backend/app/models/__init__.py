# ============================
# path: backend/app/models/__init__.py
# ============================
from __future__ import annotations

# Always export Base
from .base import Base  # noqa: F401

# Import submodules for mapper registration side effects
from . import skip as _skip_models      # noqa: F401
from . import labels as _label_models   # noqa: F401
try:
    from . import models as _core_models  # noqa: F401  # holds SkipPlacement in some branches
except Exception:
    _core_models = None  # type: ignore

# Stable re-exports
from .skip import Skip, SkipStatus              # noqa: F401
from .labels import SkipAsset, SkipAssetKind    # noqa: F401

# Robust SkipPlacement re-export: try models.py first, then skip.py
SkipPlacement = None  # type: ignore[assignment]
try:
    from .models import SkipPlacement as _SP  # type: ignore
    SkipPlacement = _SP  # type: ignore[assignment]
except Exception:
    try:
        from .skip import SkipPlacement as _SP  # type: ignore
        SkipPlacement = _SP  # type: ignore[assignment]
    except Exception:
        # leave as None; some builds may not ship this model
        pass

__all__ = ["Base", "Skip", "SkipStatus", "SkipAsset", "SkipAssetKind"]
if SkipPlacement is not None:  # pragma: no cover
    __all__.append("SkipPlacement")
