#!/bin/bash

. "/etc/parallelcluster/cfnconfig"

echo "post-install script has $# arguments"
for arg in "$@"
do
    echo "arg: ${arg}"
done

# Enables qstat for slurm
apt install -y libswitch-perl

# Override with $2 if set, or use default paths
spack_install_path=${2:-/shared/spack-0.13}
accounting_log_path=${3:-/opt/slurm/log}
accounting_log_file=${4:-sacct.log}

env > /opt/user_data_env.txt

case "${cfn_node_type}" in
    MasterServer)
        # Setup spack on master:
        git clone https://github.com/spack/spack -b releases/v0.13 ${spack_install_path}

        # On both: load spack at login
        echo ". ${spack_install_path}/share/spack/setup-env.sh" > /etc/profile.d/spack.sh
        echo ". ${spack_install_path}/share/spack/setup-env.csh" > /etc/profile.d/spack.csh

        mkdir -p ${spack_install_path}/etc/spack
        cat << EOF > ${spack_install_path}/etc/spack/packages.yaml
packages:
        openmpi:
                modules:
                        openmpi@4.0.2 fabrics=libfabric +pmi schedulers=slurm: openmpi/4.0.2
                buildable: True
        intelmpi:
                modules:
                        intelmpi@2019.6.166: intelmpi/2019.6.166
                buildable: True
        slurm:
                paths:
                        slurm@19.05.5: /opt/slurm/
                buildable: False
        libfabric:
                modules:
                        libfabric@1.9.0 fabrics=efa: libfabric/1.9.0amzn1.1
                buildable: True
EOF
	cat << EOF > ${spack_install_path}/etc/spack/modules.yaml
modules:
  tcl:
    verbose: True
    hash_length: 0
    naming_scheme: '{name}/{version}-{compiler.name}-{compiler.version}'
    all:
      conflict:
        - '{name}'
      suffixes:
        '^openblas': openblas
        '^netlib-lapack': netlib
      filter:
        environment_blacklist: ['CPATH', 'LIBRARY_PATH']
      environment:
        set:
          '{name}_ROOT': '{prefix}'
    gcc:
      environment:
        set:
          CC: gcc
          CXX: g++
          FC: gfortran
          F90: gfortran
          F77: gfortran
    netlib-scalapack:
      suffixes:
        '^openmpi': openmpi
        '^mpich': mpich
    ^python:
      autoload:  direct
EOF
	chown -R ubuntu:ubuntu ${spack_install_path}
    chmod -R go+rwX ${spack_install_path}

    #. /etc/profile.d/spack.sh
	su - ubuntu -c ". /etc/profile && spack bootstrap"
	su - ubuntu -c ". /etc/profile && spack install miniconda3 && conda upgrade conda -y"

    mkdir -p ${accounting_log_path}
    chmod 755 ${accounting_log_path}
    touch ${accounting_log_path}/${accounting_log_file}
    chmod 644 ${accounting_log_path}/${accounting_log_file}
    chmod slurm:slurm ${accounting_log_path}/${accounting_log_file}
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

    chown slurm:slurm ${accounting_log_path}/${accounting_log_file}

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
