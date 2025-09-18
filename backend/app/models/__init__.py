from __future__ import annotations

# Export Base so "from app.models import Base" works
from .base import Base  # noqa: F401

# Load submodules for mapper registration side-effects
from . import skip as _skip_models      # noqa: F401
from . import labels as _label_models   # noqa: F401
try:
    from . import models as _core_models  # noqa: F401  # may host SkipPlacement in some branches
except Exception:
    _core_models = None  # type: ignore

# Stable re-exports (the *only* surface consumers should import from)
from .skip import Skip, SkipStatus              # noqa: F401
from .labels import SkipAsset, SkipAssetKind    # noqa: F401

# Robust re-export for SkipPlacement: try both homes, don't crash import
try:
    from .models import SkipPlacement  # noqa: F401
except Exception:  # pragma: no cover
    try:
        from .skip import SkipPlacement  # type: ignore  # noqa: F401
    except Exception:
        # Leave undefined; callers must not import it from app.models unless present
        pass

__all__ = [
    "Base",
    "Skip", "SkipStatus",
    "SkipAsset", "SkipAssetKind",
    "SkipPlacement",  # may be absent if model isn't in this build
]
