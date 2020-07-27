# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import setuptools
from pcluster import __version__

with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="pcluster",
    version=__version__,

    description="Creates the building blocks for a HPC Cluster",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="sean-smith",

    package_dir={"": "pcluster"},
    packages=setuptools.find_packages(where="pcluster"),

    install_requires=[
        "aws-cdk.core>=1.31.0",
        "aws-cdk.aws-cloud9>=1.31.0",
        "aws-cdk.aws-cloudtrail>=1.31.0",
        "aws-cdk.aws-s3>=1.31.0",
        "aws-cdk.aws-s3-assets>=1.31.0",
        "aws-cdk.aws-lambda>=1.31.0",
        "aws-cdk.aws-cloudformation>=1.31.0",
        "aws-cdk.custom-resources>=1.31.0",
        "aws-cdk.aws-secretsmanager>=1.31.0",
        "aws-cdk.aws-budgets>=1.31.0",
        'importlib-metadata ~= 1.0 ; python_version < "3.8"',
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
