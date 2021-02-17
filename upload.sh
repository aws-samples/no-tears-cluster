#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

set -e

# Run this file to copy all required assets into $s3_bucket as well as ${s3_bucket}-${region}
# for all regions and make cfn.yaml reference those assets.

# Example execution:
#
#  sh upload.sh my-test-bucket-name

# Output cfn.yaml : Can be used on a new clean account by a different user.

s3_bucket=${1:-notearshpc-quickstart}
version=$( python setup.py --version )

# Edit cfn.yaml to include correct bucket
edit_cfn()
{
    awk -v s3=${s3_bucket} '1;/Description: S3 bucket for asset/{ print "    Default: \"" s3 "\""}' cfn.yaml > cfn-changed.yaml
    mv cfn-changed.yaml cfn.yaml
}

upload()
{
    # Report id, local path and s3_key for each asset
    eval "$(python3 report_s3.py ${s3_bucket})"

    for ((i=0; i<${#asset_id[@]}; i++))
    do
	# DEBUG echo "${asset_id[$i]} ${asset_key[$i]}"
	# Edit cfn.yaml to include correct keys
	awk -v key=${version}/${asset_key[$i]}  '1;/Description: S3 key for asset version "'${asset_id[$i]}'"/{ print "    Default: \"" key "||\""}' cfn.yaml > cfn-changed.yaml
	mv cfn-changed.yaml cfn.yaml

	# Edit to point to correct region
	# note: /usr/bin/sed is the correct version of sed on a mac, it may vary on linux
	/usr/bin/sed -e "s/Ref: ${asset_bucket_param[$i]}/!FindInMap [RegionMap, !Ref 'AWS::Region', RegionBucket]/g" -i '' cfn.yaml
    done
}

# Upload default AWS ParallelCluster config file
upload_config()
{
	aws s3 cp --acl public-read scripts/config.ini s3://${s3_bucket}/${version}/config.ini
	aws s3 cp --recursive --acl public-read scripts/spack s3://${s3_bucket}/${version}/spack
}

upload_cfn()
{
	if ! $(aws s3 ls s3://${s3_bucket} &> /dev/null)
	then
	   aws s3 mb s3://${s3_bucket}
	fi
 	aws s3 cp --acl public-read cfn.yaml s3://${s3_bucket}/${version}/cfn.yaml
}

# Upload lambdas in every part of the world and make cfn.yaml aware of their locations
upload_lambda_worldwide()
{
    # Add newline after Mappings
    echo "

$(cat cfn.yaml)
" > cfn.yaml

    for region in $( aws ec2 describe-regions --query 'Regions[].RegionName' --output text)
    do
	if ! $(aws s3 ls s3://${s3_bucket}-${region} &> /dev/null)
	then
	   aws s3 mb s3://${s3_bucket}-${region} --region ${region}
	fi
 	aws s3 cp --acl public-read --recursive s3://${s3_bucket}/${version}/asset s3://${s3_bucket}-${region}/${version}/asset/

	echo "    ${region}:
      RegionBucket: ${s3_bucket}-${region}
$(cat cfn.yaml)
" > cfn.yaml
    done

    echo "Mappings:
  RegionMap:
$(cat cfn.yaml)
"  > cfn.yaml

}


cdk synthesize > cfn.yaml
edit_cfn
upload
upload_lambda_worldwide
upload_cfn
upload_config
echo "Use cfn.yaml for CloudFormation"
