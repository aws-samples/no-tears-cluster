#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import core

from pcluster.pcluster_stack import PclusterStack


app = core.App()
PclusterStack(app, "pcluster")

app.synth()
