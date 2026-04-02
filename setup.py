"""Setup shim — package metadata and dependencies live in pyproject.toml."""

from setuptools import setup, find_packages

setup(
    packages=find_packages(
        exclude=["tests", "tests.*", "tools", "demos", "reference", "agents"]
    ),
)
