#!/usr/bin/env bash


sudo pip-3.6 --disable-pip-version-check --no-cache-dir install aws-parallelcluster -U

export AWS_DEFAULT_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone | rev | cut -c 2- | rev)

# Create and load ssh key
aws ec2 create-key-pair \
    --key-name pcluster_key \
    --query KeyMaterial \
    --output text > ~/.ssh/pcluster_key
chmod 600 ~/.ssh/pcluster_key

# Automatically add ssh key into agent. we need to make the agent stop asking for a password
echo 'eval `ssh-agent`' >> ~/.bashrc
echo 'ssh-add ~/.ssh/pcluster_key' >> ~/.bashrc

mkdir -p ~/.parallelcluster
cat >> ~/.parallelcluster/config <<EOF
[global]
cluster_template = covid
update_check = true
sanity_check = true

[aws]
aws_region_name = ${AWS_DEFAULT_REGION}

[aliases]
ssh = ssh {CFN_USER}@{MASTER_IP} {ARGS}

[cluster covid]
key_name = pcluster_key
base_os = ubuntu1804
scheduler = slurm
master_instance_type = c5n.9xlarge
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
vpc_id = ${vpc_id}
master_subnet_id = ${master_subnet_id}
compute_subnet_id = ${compute_subnet_id}

EOF


# screen decouples the pcluster command so that the Cloud9 CFN template does not time out
# pcluster is for some reason not ine th path.
screen -d -m /usr/local/bin/pcluster create -t covid covid-cluster
