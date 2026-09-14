from setuptools import setup, find_packages

setup(
    name="coldguard",
    version="0.1.0",
    description="Kinetic-Bayesian vaccine potency estimation for cold chain management",
    author="ColdGuard Team",
    license="MIT",
    packages=find_packages(exclude=["tests*", "notebooks*"]),
    python_requires=">=3.11",
    install_requires=[
        "numpy>=1.26.0",
        "scipy>=1.11.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "plotly>=5.15.0",
        "streamlit>=1.25.0",
        "reportlab>=4.0.0",
        "pydantic>=2.13.5",
        "python-dateutil>=2.8.2",
    ],
    extras_require={
        "dev": ["pytest>=7.4.0", "jupyter>=1.0.0"],
    },
    entry_points={
        "console_scripts": [
            "coldguard=core.utils:cli_main",
        ],
    },
)
