from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="qz7-shell",
    description="Utility functions to run code on local and remote systems.",

    author="Parantapa Bhattacharya",
    author_email="pb+pypi@parantapa.net",

    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=["qz7.shell"],

    use_scm_version=True,
    setup_requires=['setuptools_scm'],

    install_requires=[
        "paramiko"
    ],

    url="http://github.com/parantapa/qz7-shell",
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
