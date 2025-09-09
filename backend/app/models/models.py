# path: backend/app/models/models.py
from __future__ import annotations
from dataclasses import dataclass

# Re-export ONLY — do not declare models here.
from .skip import Skip
from .labels import SkipAsset, SkipAssetKind

class UserRole:
    admin = "admin"
    driver = "driver"
    dispatcher = "dispatcher"
    user = "user"

@dataclass
class User:
    id: str
    role: str

__all__ = ["Skip", "SkipAsset", "SkipAssetKind", "User", "UserRole"]
