"""
This package provides a simple interface for caching data to disk.
It uses JSON files to store data, with each file representing a cache entry.
"""

from .cache_manager import load_data, save_data, delete_data

__all__ = ["load_data", "save_data", "delete_data"]
