s3_bucket=seaam
region=us-east-1
azs="$(region)a\,$(region)b"
stack_name=pcluster
bootstrapS3URI=s3://${s3_bucket}/bootstrap.sh

all: create

upload:
	aws s3 cp templates/cloud9-ide-master.template.yaml s3://${s3_bucket}/cloud9-ide-master.template.yaml
	aws s3 cp --acl public-read scripts/bootstrap.sh ${bootstrapS3URI}

wait_network: 
	aws cloudformation wait stack-create-complete --stack-name VPCStack 

exists_network:  
	aws cloudformation wait stack-exists --stack-name VPCStack 

network:
	aws s3 cp templates/aws-vpc.template.yaml s3://${s3_bucket}/aws-vpc.template.yaml
	aws cloudformation create-stack --region ${region} --stack-name VPCStack \
	 --template-url https://${s3_bucket}.s3-${region}.amazonaws.com${s3_suffix}/aws-vpc.template.yaml --capabilities CAPABILITY_IAM \
 	 --parameters ParameterKey=AvailabilityZones,ParameterValue=${azs}

try_network:
	$(MAKE) exists_network || $(MAKE) network
	$(MAKE) wait_network 

create: try_network upload
	aws cloudformation create-stack --region ${region} --stack-name ${stack_name} \
 	 --template-url https://${s3_bucket}.s3-${region}.amazonaws.com${s3_suffix}/cloud9-ide-master.template.yaml --capabilities CAPABILITY_IAM \
 	 --parameters ParameterKey=AvailabilityZones,ParameterValue=${azs} \
 	 			  ParameterKey=VPCStackName,ParameterValue=VPCStack \
				  ParameterKey=BootstrapS3URI,ParameterValue=${bootstrapS3URI} \
 	 --disable-rollback
