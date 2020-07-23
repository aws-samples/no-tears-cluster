#!/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import json
import sys

from pcluster import __version__

def main():

    manifest = json.load(open("cdk.out/manifest.json"))
    bucket = sys.argv[1]

    asset_id = []
    asset_key = []
    asset_bucket_param = []

    for asset in manifest['artifacts']['pcluster']['metadata']['/pcluster']:
        asset_id.append(asset['data']['id'])
        path = asset['data']['path']
        asset_bucket_param.append(asset['data']['s3BucketParameter'])
        asset_key.append("placeholder")

        if asset['data']['packaging'] == "zip":
            # For directories
            print("cd cdk.out/{p}; zip -r ../{i}.zip *; cd ../..".
                  format(p=path, i=asset_id[-1]))
            print("aws s3 cp --acl public-read cdk.out/{i}.zip s3://{b}/{v}/asset/".
                  format(p=path, b=bucket, i=asset_id[-1], v=__version__))

            asset_key[-1] = ".".join([asset_id[-1], "zip"])
            asset_key[-1] = "/".join(["asset", asset_key[-1]])

        elif asset['data']['packaging'] == "file":
            # For single files
            print("aws s3 cp --acl public-read cdk.out/{p} s3://{b}/{v}/{k}".
                  format(p=path, b=bucket, k=path.replace(".", "/", 1), v=__version__))

            asset_key[-1] = path.replace(".", "/", 1)

        else:
            print("Unknown packaging format {}".format(asset['data']['packaging']))

    print("declare -a asset_id; asset_id=({})".format(" ".join(asset_id)))
    print("declare -a asset_key; asset_key=({})".format(" ".join(asset_key)))
    print("declare -a asset_bucket_param; asset_bucket_param=({})".format(" ".join(asset_bucket_param)))


main()
