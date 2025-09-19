# backend/app/models/__init__.py
from .base import Base  # noqa: F401
from . import skip as _skip_models   # noqa: F401
from . import labels as _label_models  # noqa: F401
try:
    from . import models as _core_models  # noqa: F401
except Exception:
    _core_models = None  # type: ignore

from .skip import Skip, SkipStatus  # noqa: F401
from .labels import SkipAsset, SkipAssetKind  # noqa: F401

SkipPlacement = None  # type: ignore
try:
    from .models import SkipPlacement as _SP  # type: ignore
    SkipPlacement = _SP
except Exception:
    try:
        from .skip import SkipPlacement as _SP  # type: ignore
        SkipPlacement = _SP
    except Exception:
        pass

__all__ = ["Base", "Skip", "SkipStatus", "SkipAsset", "SkipAssetKind"]
if SkipPlacement is not None:
    __all__.append("SkipPlacement")
