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
        asset_key.append(asset['data']['s3KeyParameter'])

        # For single files
        print("aws s3 cp --acl public-read cdk.out/{p} s3://{b}/{k}".
              format(p=path, b=bucket, k=asset_key[-1]))
        # For direcotries
        print("aws s3 cp --recursive --acl public-read cdk.out/{p} s3://{b}/{k}".
              format(p=path, b=bucket, k=asset_key[-1]))

    print("declare -a asset_id; asset_id=({})".format(" ".join(asset_id)))
    print("declare -a asset_key; asset_key=({})".format(" ".join(asset_key)))

main()
