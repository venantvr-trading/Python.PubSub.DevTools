"""
Setup script for PubSub Dev Tools

This exists for backwards compatibility with older pip versions.
Modern installations should use pyproject.toml.
"""
from setuptools import setup, find_packages

setup(
    name="python-pubsub-devtools",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask>=2.0.0",
        "pyyaml>=6.0",
        "pydantic>=2.0",
    ],
    entry_points={
        'console_scripts': [
            'pubsub-tools=python_pubsub_devtools.cli.main:main',
        ],
    },
)
