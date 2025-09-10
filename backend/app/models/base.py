# path: backend/app/models/base.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Single declarative base for the whole project."""
    pass
