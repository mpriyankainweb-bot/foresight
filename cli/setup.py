from setuptools import find_packages, setup

setup(
    name="foresight-cli",
    version="0.1.0",
    description="Foresight Deploy-Safety CLI",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.27.0",
    ],
    entry_points={
        "console_scripts": [
            "foresight=foresight_cli.main:cli",
        ],
    },
)
