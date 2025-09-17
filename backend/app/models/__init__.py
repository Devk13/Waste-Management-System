from __future__ import annotations

from .base import Base  # so "from app.models import Base" works

# load submodules for mapper registration side-effects
from . import skip as _skip_models      # noqa: F401
from . import labels as _label_models   # noqa: F401
try:
    from . import models as _core_models  # holds SkipPlacement in this repo
except Exception:
    _core_models = None  # noqa: F841

# stable re-exports (single public surface)
from .skip import Skip, SkipStatus                 # noqa: F401
from .labels import SkipAsset, SkipAssetKind       # noqa: F401
from .models import SkipPlacement                  # noqa: F401  <-- key line

__all__ = [
    "Base",
    "Skip", "SkipStatus",
    "SkipAsset", "SkipAssetKind",
    "SkipPlacement",
]
