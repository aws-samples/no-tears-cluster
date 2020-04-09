#!/usr/bin/env python3

from aws_cdk import core

from pcluster.pcluster_stack import PclusterStack


app = core.App()
PclusterStack(app, "pcluster")

app.synth()
