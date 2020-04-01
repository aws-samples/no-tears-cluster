#!/usr/bin/env bash

pip-3.6 install aws-parallelcluster -U --user
aws s3 cp  ~/.pcluster/config
