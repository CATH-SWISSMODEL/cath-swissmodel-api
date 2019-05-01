#!/usr/bin/env python

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="cathsm",
    version="0.0.1",
    author="Ian Sillitoe",
    author_email="i.sillitoe@ucl.ac.uk",
    description="API clients/libraries for CATH/SWISS-MODEL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CATH-SWISSMODEL/cath-swissmodel-api",
    packages=find_packages(),
    test_suite="tests",
    scripts=[
        'scripts/cathsm-api2',
    ],
    install_requires=[
        'xdg',
#        'getpass',
        'requests',
	'pyxdg',
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
