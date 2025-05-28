#!/usr/bin/env python3
"""
Setup script for Mitotic Spindle Tool
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mitotic-spindle-tool",
    version="1.0.6",
    author="Kergan Sanderson, Joe Lannan",
    author_email="",
    description="An image analysis Python GUI application for mitotic spindle analysis",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/eltinglab/mitotic-spindle-tool",
    packages=find_packages(),
    package_dir={"": "src"},
    py_modules=[
        "spindleGUI",
        "curveFitData",
        "plotSpindle",
        "plotDialog",
        "manualSpindleDialog",
        "spindlePreviewDialog",
        "threshFunctions",
        "tiffFunctions"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "mitotic-spindle-tool=spindleGUI:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
