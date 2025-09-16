# path: backend/app/models/__init__.py
from .base import Base  # re-export Base so "from app.models import Base" works

# Import model modules for their mapper side-effects (table registration)
from . import skip as _skip_models  # noqa: F401
from . import labels as _label_models  # noqa: F401

# Optional: export classes if you want
from .skip import Skip, SkipStatus  # noqa: F401
from .labels import SkipAsset, SkipAssetKind  # noqa: F401

# Ensure mapper registry knows both classes before first use
from . import skip as _skip     # noqa: F401  side-effect: defines class Skip
from . import labels as _labels # noqa: F401  side-effect: defines class SkipAsset

__all__ = ["Base"]