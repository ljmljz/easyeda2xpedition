from setuptools import setup, find_packages

setup(
    name="easyeda2xpedition",
    version="0.1.0",
    description="Convert EasyEDA footprint to Xpedition hkp files",
    author="Jimmy Li",
    packages=find_packages(),
    install_requires=[
        "PyQt5",
        "requests",
        "pydantic",
    ],
    python_requires=">=3.7",
    include_package_data=True,
    entry_points={
        "console_scripts": [
            # Example: 'easyeda2xpedition=easyeda2xpedition.cli:main',
        ]
    },
)
