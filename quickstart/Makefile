s3_bucket=ebbollig-pcluster-userdata-120988395753
region=us-west-2
azs="us-west-2a\,us-west-2b"
stack_name=pcluster

all: create

upload:
	aws s3 cp templates/cloud9-ide-master.template.yaml s3://${s3_bucket}/cloud9-ide-master.template.yaml
	aws s3 cp --acl public-read scripts/bootstrap.sh s3://${s3_bucket}/bootstrap.sh

wait_network: 
	aws cloudformation wait stack-create-complete --stack-name VPCStack 

exists_network:  
	aws cloudformation wait stack-exists --stack-name VPCStack 

network:
	aws s3 cp templates/aws-vpc.template.yaml s3://${s3_bucket}/aws-vpc.template.yaml
	aws cloudformation create-stack --region ${region} --stack-name VPCStack \
	 --template-url https://s3.${region}.amazonaws.com${s3_suffix}/${s3_bucket}/aws-vpc.template.yaml --capabilities CAPABILITY_IAM \
 	 --parameters ParameterKey=AvailabilityZones,ParameterValue=${azs}

try_network:
	$(MAKE) exists_network || $(MAKE) network
	$(MAKE) wait_network 

create: try_network upload
	aws cloudformation create-stack --region ${region} --stack-name ${stack_name} \
 	 --template-url https://s3.${region}.amazonaws.com${s3_suffix}/${s3_bucket}/cloud9-ide-master.template.yaml --capabilities CAPABILITY_IAM \
 	 --parameters ParameterKey=AvailabilityZones,ParameterValue=${azs} \
 	 			  ParameterKey=VPCStackName,ParameterValue=VPCStack \
 	 --disable-rollback
