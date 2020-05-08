#!/bin/bash

set -e

# Run this file to copy all required assets into $s3_bucket as well as ${s3_bucket}-${region}
# for all regions and make cfn.yaml reference those assets.

# Output cfn.yaml : Can be used on a new clean account by a different user.

s3_bucket=${1:-notearshpc-quickstart} #8192-stesachs #covid19hpc-bucket-stesachs #covid19hpc-quickstart-161153343288

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
	awk -v key=${asset_key[$i]}  '1;/Description: S3 key for asset version "'${asset_id[$i]}'"/{ print "    Default: \"" key "||\""}' cfn.yaml > cfn-changed.yaml
	mv cfn-changed.yaml cfn.yaml

	# Edit to point to correct region
	sed -e "s/Ref: ${asset_bucket_param[$i]}/!FindInMap [RegionMap, !Ref 'AWS::Region', RegionBucket]/g" -i '' cfn.yaml
    done
}

upload_cfn()
{
	if ! $(aws s3 ls s3://${s3_bucket} &> /dev/null)
	then
	   aws s3 mb s3://${s3_bucket}
	fi
 	aws s3 cp --acl public-read cfn.yaml s3://${s3_bucket}/cfn.yaml
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
 	aws s3 cp --acl public-read --recursive s3://${s3_bucket}/asset s3://${s3_bucket}-${region}/asset/

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
echo "Use cfn.yaml for CloudFormation"
