"""Setup configuration for Interphyre package."""

from setuptools import setup, find_packages
import re

# Read version from __init__.py
with open("interphyre/__init__.py", "r") as f:
    version = re.search(r'__version__ = ["\']([^"\']+)["\']', f.read()).group(1)

# Read long description from README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="interphyre",
    version=version,
    author="Sankaran Vaidyanathan",
    author_email="sankaran.vaidyanathan@example.com",  # Update with actual email
    description="Physics-based puzzle environment for reinforcement learning and causal inference",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sankaranv/interphyre",
    packages=find_packages(exclude=["tests", "tests.*", "tools", "demos", "reference", "agents"]),
    python_requires=">=3.10",
    install_requires=[
        "box2d-py>=2.3.8",
        "gymnasium>=0.29.1",
        "matplotlib>=3.10.0",
        "numpy>=1.26.0,<2.0.0",
        "opencv-python>=4.8.0",
        "Pillow>=10.0.0",
        "pygame>=2.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov",
        ],
        "ml": [
            "torch>=2.1.0",
            "transformers>=4.40.0",
            "peft>=0.11.1",
            "accelerate>=0.25.0",
            "timm>=0.9.10,<1.0.0",
            "einops>=0.7.0",
        ],
        "data": [
            "pandas>=2.0.0",
            "tensorboard>=2.15.0",
            "tqdm>=4.66.0",
            "psutil>=7.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
