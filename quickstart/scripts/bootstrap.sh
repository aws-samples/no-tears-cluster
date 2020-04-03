#!/usr/bin/env bash


pip-3.6 --disable-pip-version-check install aws-parallelcluster -U


AWS_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone | sed 's/.$//')
KEY_NAME=$1
VPC_STACK=VPCStack

mkdir -p $HOME/.parallelcluster
cat >> $HOME/.parallelcluster/config <<EOF
[global]
cluster_template = covid
update_check = true
sanity_check = true

[aws]
aws_region_name = ${AWS_REGION}

[aliases]
ssh = ssh {CFN_USER}@{MASTER_IP} {ARGS}

[cluster covid]
key_name = ${KEY_NAME}
base_os = ubuntu1804
scheduler = slurm
master_instance_type = c5n.18xlarge
compute_instance_type = c5n.18xlarge
vpc_settings = public-private
fsx_settings = fsx
disable_hyperthreading = true
dcv_settings = dcv
post_install = https://covid19hpc-quickstart-161153343288.s3.amazonaws.com/user_data.sh

[fsx fsx]
shared_dir = /fsx
storage_capacity = 1200

[dcv dcv]
enable = master
port = 8443
access_from = 0.0.0.0/0

[vpc public-private]
vpc_id = $(aws --region ${AWS_REGION} cloudformation  describe-stacks --stack-name ${VPC_STACK} --query "Stacks[0].Outputs[?OutputKey=='VPCID'].OutputValue" --output=text)
master_subnet_id = $(aws --region ${AWS_REGION} cloudformation  describe-stacks --stack-name ${VPC_STACK} --query "Stacks[0].Outputs[?OutputKey=='PublicSubnet1ID'].OutputValue" --output=text)
compute_subnet_id = $(aws --region ${AWS_REGION} cloudformation  describe-stacks --stack-name ${VPC_STACK} --query "Stacks[0].Outputs[?OutputKey=='PrivateSubnet1AID'].OutputValue" --output=text)

EOF