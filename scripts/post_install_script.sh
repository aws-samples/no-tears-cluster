#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
set +e

exec &> >(tee -a "/tmp/post_install.log")

. "/etc/parallelcluster/cfnconfig"

echo "post-install script has $# arguments"
for arg in "$@"
do
    echo "arg: ${arg}"
done

# Enables qstat for slurm
YUM_CMD=$(which yum)
APT_GET_CMD=$(which apt-get)
if [[ ! -z $YUM_CMD ]]; then
    wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm -P /tmp
    yum install -y /tmp/epel-release-latest-7.noarch.rpm

    yum install -y perl-Switch python3 python3-pip links
    getent passwd ec2-user > /dev/null 2&>1
    if [ $? -eq 0 ]; then
        OSUSER=ec2-user
        OSGROUP=ec2-user
    else
        OSUSER=centos
        OSGROUP=centos
    fi

    # Add nvidia-docker if possible
    nvidia-smi -L > /dev/null
    if [ $? -eq 0  ]; then
     distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
     curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.repo | tee /etc/yum.repos.d/nvidia-docker.repo
     yum install -y nvidia-docker2
     groupadd docker
     usermod -aG docker $OSUSER
     systemctl restart docker
    fi
elif [[ ! -z $APT_GET_CMD ]]; then
    apt-get update
    apt-get install -y libswitch-perl python3 python3-pip links
    OSUSER=ubuntu
    OSGROUP=ubuntu

    # Add nvidia-docker if possible
    nvidia-smi -L > /dev/null
    if [ $? -eq 0  ]; then
     distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
     curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add - && distribution=$(. /etc/os-release;echo $ID$VERSION_ID) && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list && apt-get update && apt-get install -y nvidia-docker2 && pkill -SIGHUP dockerd
     groupadd docker
     usermod -aG docker $OSUSER
     systemctl restart docker
    fi
else
    echo "error can't install package $PACKAGE"
    exit 1;
fi

pip3 install --upgrade awscli boto3

# Override with $2 if set, or use default paths
spack_install_path=${2:-/shared/spack}
spack_tag=${3:-releases/v0.16}
spack_config_uri=${4:-https://notearshpc-quickstart.s3.amazonaws.com/0.2.0/spack}
accounting_log_path=${5:-/opt/slurm/log}
accounting_log_file=${6:-sacct.log}

env > /opt/user_data_env.txt

case "${cfn_node_type}" in
    MasterServer)

        export AWS_DEFAULT_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone | rev | cut -c 2- | rev)
        aws configure set default.region ${AWS_DEFAULT_REGION}
        aws configure set default.output json

        # Setup spack on master:
        git clone https://github.com/spack/spack -b ${spack_tag} ${spack_install_path}

        # On both: load spack at login
        echo ". ${spack_install_path}/share/spack/setup-env.sh" > /etc/profile.d/spack.sh
        echo ". ${spack_install_path}/share/spack/setup-env.csh" > /etc/profile.d/spack.csh

        mkdir -p ${spack_install_path}/etc/spack
        # V2.0 borrowed "all:" block from https://spack-tutorial.readthedocs.io/en/latest/tutorial_configuration.html

        # Autodetect OPENMPI, INTELMPI, SLURM, LIBFABRIC and GCC versions to inform Spack of available packages.
        # e.g., OPENMPI_VERSION=4.0.3
        export OPENMPI_VERSION=$(. /etc/profile && module avail openmpi 2>&1 | grep openmpi | head -n 1 | cut -d / -f 2)
        # e.g., INTELMPI_VERSION=2019.7.166
        export INTELMPI_VERSION=$(. /etc/profile && module show intelmpi 2>&1 | grep I_MPI_ROOT | sed 's/[[:alpha:]|_|:|\/|(|[:space:]]//g' | awk -F- '{print $1}' )
        # e.g., SLURM_VERSION=19.05.5
        export SLURM_VERSION=$(. /etc/profile && sinfo --version | cut -d' ' -f 2)
        # e.g., LIBFABRIC_VERSION=1.10.0
        # e.g., LIBFABRIC_MODULE=1.10.0amzn1.1
        export LIBFABRIC_MODULE=$(. /etc/profile && module avail libfabric 2>&1 | grep libfabric | head -n 1 )
        export LIBFABRIC_MODULE_VERSION=$(. /etc/profile && module avail libfabric 2>&1 | grep libfabric | head -n 1 |  cut -d / -f 2 )
        export LIBFABRIC_VERSION=${LIBFABRIC_MODULE_VERSION//amzn*}
        # e.g., GCC_VERSION=7.3.5
        export GCC_VERSION=$( gcc -v 2>&1 |tail -n 1| awk '{print $3}' )

        #NOTE: as of parallelcluster v2.8.0, SLURM is built with PMI3

        echo "Pulling Config: ${spack_config_uri}"
        case "${spack_config_uri}" in
            s3://*)
                aws s3 cp ${spack_config_uri}/packages.yaml /tmp/packages.yaml --quiet;
                aws s3 cp ${spack_config_uri}/modules.yaml /tmp/modules.yaml --quiet;
                aws s3 cp ${spack_config_uri}/mirrors.yaml /tmp/mirrors.yaml --quiet;;
            http://*|https://*)
                wget ${spack_config_uri}/packages.yaml -O /tmp/packages.yaml -o /tmp/debug_spack.wget;
                wget ${spack_config_uri}/modules.yaml -O /tmp/modules.yaml -a /tmp/debug_spack.wget;
                wget ${spack_config_uri}/mirrors.yaml -O /tmp/mirrors.yaml -a /tmp/debug_spack.wget;;
            *)
                echo "Unknown/Unsupported spack packages URI"
                ;;
        esac
        envsubst < /tmp/packages.yaml > ${spack_install_path}/etc/spack/packages.yaml
        cat ${spack_install_path}/etc/spack/packages.yaml

        envsubst < /tmp/modules.yaml > ${spack_install_path}/etc/spack/modules.yaml
        cat ${spack_install_path}/etc/spack/modules.yaml

        envsubst < /tmp/mirrors.yaml > ${spack_install_path}/etc/spack/mirrors.yaml
        cat ${spack_install_path}/etc/spack/mirrors.yaml

    echo "OSUSER=${OSUSER}"
    echo "OSGROUP=${OSGROUP}"
	chown -R ${OSUSER}:${OSGROUP} ${spack_install_path}
    chmod -R go+rwX ${spack_install_path}

    #. /etc/profile.d/spack.sh
    su - ${OSUSER} -c ". /etc/profile && curl -o /tmp/amzn2-e4s.pub https://s3.amazonaws.com/spack-mirrors/amzn2-e4s/build_cache/_pgp/7D344E2992071B0AAAE1EDB0E68DE2A80314303D.pub && spack gpg trust /tmp/amzn2-e4s.pub"
    su - ${OSUSER} -c ". /etc/profile && spack install miniconda3"
    su - ${OSUSER} -c ". /etc/profile && module load miniconda3 && conda upgrade conda -y"

    mkdir -p ${accounting_log_path}
    chmod 755 ${accounting_log_path}
    touch ${accounting_log_path}/${accounting_log_file}
    chmod 644 ${accounting_log_path}/${accounting_log_file}
    chown slurm:slurm ${accounting_log_path}/${accounting_log_file}
    cat << EOF > /opt/slurm/etc/enable_sacct.conf

JobAcctGatherType=jobacct_gather/linux
JobAcctGatherFrequency=30
#
#AccountingStorageType=accounting_storage/slurmdbd
AccountingStorageType=accounting_storage/filetxt
#AccountingStorageHost=
#AccountingStorageLoc=
AccountingStorageLoc=${accounting_log_path}/${accounting_log_file}
#AccountingStoragePass=
#AccountingStorageUser=

MinJobAge=172800
EOF
    grep -qxF 'include enable_sacct.conf' /opt/slurm/etc/slurm.conf || echo 'include enable_sacct.conf' >> /opt/slurm/etc/slurm.conf

    systemctl restart slurmctld.service

    ;;
    ComputeFleet)
        # On both: load spack at login
        echo ". ${spack_install_path}/share/spack/setup-env.sh" > /etc/profile.d/spack.sh
        echo ". ${spack_install_path}/share/spack/setup-env.csh" > /etc/profile.d/spack.csh
    ;;
    *)
    ;;
esac

