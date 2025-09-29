from setuptools import setup, find_packages

setup(
    name='LGS_Stock_Backend',
    version='0.1.0',
    packages=find_packages(),
    entry_points={
        'paste.app_factory': [
            'main = run:create_app',
        ],
    }
)
