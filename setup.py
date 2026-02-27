from setuptools import setup, find_packages

setup(
    name="easyeda2xpedition",
    version="0.1.0",
    description="Convert EasyEDA footprint and symbols to Mentor Graphics Xpedition format",
    author="Jimmy Li",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15.0",
        "requests>=2.25.0",
        "pydantic>=1.8.0",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    entry_points={
        "console_scripts": [
            # Example: 'easyeda2xpedition=easyeda2xpedition.cli:main',
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
)
