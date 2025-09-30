"""Configuration utilities for Filtra."""
from __future__ import annotations

from .alias_map import AliasMap, AliasMapDetails, DEFAULT_ALIAS_MAP_PATH, load_alias_map

__all__ = [
    "AliasMap",
    "AliasMapDetails",
    "DEFAULT_ALIAS_MAP_PATH",
    "load_alias_map",
]