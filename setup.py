from setuptools import setup, find_packages

setup(
    name='LGS_Stock_Backend',
    version='0.1.0',
    # Explicitly list the packages to include, instead of using find_packages().
    # This resolves the "flat-layout" ambiguity for setuptools.
    packages=[
        'config',
        'data',
        'externals',
        'managers',
        'routes',
        'tasks',
        'utility'
    ],
    entry_points={
        'paste.app_factory': [
            'main = run:create_app',
        ],
    }
)
