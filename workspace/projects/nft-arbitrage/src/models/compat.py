"""
Compatibility helpers for SQLAlchemy models.
Provides utility functions for serialisation, filtering, and common patterns
that work across both SQLite (dev) and PostgreSQL (production).
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional


def model_to_dict(instance, exclude: Optional[set] = None) -> Dict[str, Any]:
    """Convert a SQLAlchemy model instance to a plain dictionary.

    Args:
        instance: The SQLAlchemy model instance.
        exclude: Optional set of column names to exclude.

    Returns:
        Dictionary of column names to values.
    """
    exclude = exclude or set()
    result = {}
    for col in instance.__table__.columns:
        if col.name in exclude:
            continue
        value = getattr(instance, col.name)
        # Convert types that are not JSON-serialisable by default
        if isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, datetime):
            value = value.isoformat()
        result[col.name] = value
    return result


def update_model(instance, data: Dict[str, Any], allowed: Optional[set] = None):
    """Update model attributes from a dictionary.

    Args:
        instance: The SQLAlchemy model instance.
        data: Dictionary of field names to new values.
        allowed: Optional whitelist of field names that may be updated.
    """
    for key, value in data.items():
        if allowed and key not in allowed:
            continue
        if hasattr(instance, key):
            setattr(instance, key, value)


def ensure_str_uuid(value) -> str:
    """Ensure a UUID value is returned as a string."""
    if value is None:
        return value
    return str(value)
