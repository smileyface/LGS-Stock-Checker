"""
Setup script for the backend package.

This script uses setuptools to configure the package installation.
It explicitly lists the sub-packages to include, resolving any ambiguity
related to flat-layouts. The entry point for the application is defined for
PasteDeploy, specifying the factory function to create the app.

Attributes:
    name (str): The name of the package.
    version (str): The initial version of the package.
    packages (list): List of sub-packages to include in the distribution.
    entry_points (dict): Entry points for integration with PasteDeploy.
"""

from setuptools import setup


setup(
    name="backend",
    version="0.1.0",
    # Explicitly list the packages to include, instead of
    # using find_packages().
    # This resolves the "flat-layout" ambiguity for setuptools.
    packages=[
        "config",
        "data",
        "externals",
        "managers",
        "routes",
        "tasks",
        "utility",
    ],
    entry_points={
        "paste.app_factory": [
            "main = run:create_app",
        ],
    },
)
