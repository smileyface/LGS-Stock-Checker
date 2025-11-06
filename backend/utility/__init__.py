"""
This __init__.py file makes the 'utility' directory a Python package
and exposes the logger object at the top level of the package.
This allows other modules to import the logger instance directly
using `from utility import logger`.
"""
from .logger import logger

__all__ = ["logger"]