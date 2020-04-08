#!/bin/env python3
import json
import sys


def main():

    manifest = json.load(open("cdk.out/manifest.json"))
    bucket = sys.argv[1]

    asset_id = []
    asset_key = []
    
    for asset in manifest['artifacts']['pcluster']['metadata']['/pcluster']:
        asset_id.append(asset['data']['id'])
        path = asset['data']['path']
        asset_key.append("placeholder")

        if asset['data']['packaging'] == "zip":
            # For directories
            print("aws s3 cp --acl public-read cdk.out/.cache/{i}.zip s3://{b}/asset/".
                  format(p=path, b=bucket, i=asset_id[-1]))

            asset_key[-1] = ".".join([asset_id[-1], "zip"])
            asset_key[-1] = "/".join(["asset", asset_key[-1]])

        elif asset['data']['packaging'] == "file":
            # For single files
            print("aws s3 cp --acl public-read cdk.out/{p} s3://{b}/{k}".
                  format(p=path, b=bucket, k=path.replace(".", "/", 1)))

            asset_key[-1] = path.replace(".", "/", 1)

        else:
            print("Unknown packaging format {}".format(asset['data']['packaging']))

    print("declare -a asset_id; asset_id=({})".format(" ".join(asset_id)))
    print("declare -a asset_key; asset_key=({})".format(" ".join(asset_key)))


main()
