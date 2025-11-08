# setup.py
"""
Setup script for ValueCell AI Trader
"""
from setuptools import setup, find_packages

setup(
    name="valuecell-trader",
    version="1.0.0",
    description="AI-powered stock trading system built on ValueCell",
    author="ValueCell AI",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "pydantic>=2.0.0",
        "PyYAML>=6.0",
        "scikit-learn>=1.0.0",
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "feedparser>=6.0.0",
        "matplotlib>=3.5.0",
        "lxml>=4.9.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "valuecell-trader=valuecell_trader.cli:cli",
        ],
    },
    python_requires=">=3.9",
)
