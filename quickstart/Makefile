s3_bucket=seaam
region=us-east-1
azs="us-east-1a\,us-east-1b"
stack_name=pcluster

upload:
	aws s3 cp templates/cloud9-ide-master.template.yaml s3://${s3_bucket}/cloud9-ide-master.template.yaml
	aws s3 cp --acl public-read scripts/bootstrap.sh s3://${s3_bucket}/bootstrap.sh

network:
	aws s3 cp templates/aws-vpc.template.yaml s3://${s3_bucket}/aws-vpc.template.yaml
	aws cloudformation create-stack --region ${region} --stack-name VPCStack \
	 --template-url https://s3.${region}.amazonaws.com${s3_suffix}/${s3_bucket}/aws-vpc.template.yaml --capabilities CAPABILITY_IAM \
 	 --parameters ParameterKey=AvailabilityZones,ParameterValue=${azs}

create: upload
	aws cloudformation create-stack --region ${region} --stack-name ${stack_name} \
 	 --template-url https://s3.${region}.amazonaws.com${s3_suffix}/${s3_bucket}/cloud9-ide-master.template.yaml --capabilities CAPABILITY_IAM \
 	 --parameters ParameterKey=AvailabilityZones,ParameterValue=${azs} \
 	 			  ParameterKey=VPCStackName,ParameterValue=VPCStack \
 	 --disable-rollback
