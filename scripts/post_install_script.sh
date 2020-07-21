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

    yum install -y perl-Switch python3 links
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
    apt-get -y libswitch-perl python3 links
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

# Override with $2 if set, or use default paths
spack_install_path=${2:-/shared/spack}
spack_tag=${3:-releases/v0.13}
accounting_log_path=${4:-/opt/slurm/log}
accounting_log_file=${5:-sacct.log}

env > /opt/user_data_env.txt

case "${cfn_node_type}" in
    MasterServer)
        # Setup spack on master:
        git clone https://github.com/spack/spack -b ${spack_tag} ${spack_install_path}

        # On both: load spack at login
        echo ". ${spack_install_path}/share/spack/setup-env.sh" > /etc/profile.d/spack.sh
        echo ". ${spack_install_path}/share/spack/setup-env.csh" > /etc/profile.d/spack.csh

        mkdir -p ${spack_install_path}/etc/spack
        # V2.0 borrowed "all:" block from https://spack-tutorial.readthedocs.io/en/latest/tutorial_configuration.html

        #OPENMPI_VERSION=4.0.2
        OPENMPI_VERSION=$(. /etc/profile && module avail openmpi 2>&1 | grep openmpi | head -n 1 | cut -d / -f 2)
        #INTELMPI_VERSION=2019.6.166
        INTELMPI_VERSION=$(. /etc/profile && module show intelmpi 2>&1 | grep I_MPI_ROOT | sed 's/[[:alpha:]|_|:|\/|(|[:space:]]//g' | awk -F- '{print $1}' )
        #SLURM_VERSION=19.05.5
        SLURM_VERSION=$(. /etc/profile && sinfo --version | cut -d' ' -f 2)
        #LIBFABRIC_VERSION=1.9.0
        #LIBFABRIC_MODULE=1.9.0amzn1.1
        LIBFABRIC_MODULE=$(. /etc/profile && module avail libfabric 2>&1 | grep libfabric | head -n 1 )
        LIBFABRIC_MODULE_VERSION=$(. /etc/profile && module avail libfabric 2>&1 | grep libfabric | head -n 1 |  cut -d / -f 2 )
        LIBFABRIC_VERSION=${LIBFABRIC_MODULE_VERSION//amzn*}
        #GCC_VERSION=7.3.1
        GCC_VERSION=$( gcc -v 2>&1 |tail -n 1| awk '{print $3}' )

        #NOTE: we do not build openmpi with pmi support because slurm is not built for PMI
        cat << EOF > ${spack_install_path}/etc/spack/packages.yaml
packages:
        openmpi:
                modules:
                        openmpi@${OPENMPI_VERSION} fabrics=libfabric +pmi schedulers=slurm: openmpi/${OPENMPI_VERSION}
                buildable: True
        intelmpi:
                modules:
                        intelmpi@${INTELMPI_VERSION}: intelmpi
                buildable: True
        slurm:
                paths:
                        slurm@${SLURM_VERSION}: /opt/slurm/
                buildable: False
        libfabric:
                modules:
                        libfabric@${LIBFABRIC_VERSION} fabrics=efa: ${LIBFABRIC_MODULE}
                buildable: True
        all:
            compiler: [gcc, intel, pgi, clang, xl, nag, fj]
            providers:
                  D: [ldc]
                  awk: [gawk]
                  blas: [openblas]
                  daal: [intel-daal]
                  elf: [elfutils]
                  fftw-api: [fftw]
                  gl: [mesa+opengl, opengl]
                  glx: [mesa+glx, opengl]
                  glu: [mesa-glu, openglu]
                  golang: [gcc]
                  ipp: [intel-ipp]
                  java: [openjdk, jdk, ibm-java]
                  jpeg: [libjpeg-turbo, libjpeg]
                  lapack: [openblas]
                  mariadb-client: [mariadb-c-client, mariadb]
                  mkl: [intel-mkl]
                  mpe: [mpe2]
                  mpi: [openmpi, mpich]
                  mysql-client: [mysql, mariadb-c-client]
                  opencl: [pocl]
                  pil: [py-pillow]
                  pkgconfig: [pkgconf, pkg-config]
                  scalapack: [netlib-scalapack]
                  szip: [libszip, libaec]
                  tbb: [intel-tbb]
                  unwind: [libunwind]
            permissions:
                  read: world
                  write: user
EOF

    cat ${spack_install_path}/etc/spack/packages.yaml

    # Modules.yaml from https://spack-tutorial.readthedocs.io/en/latest/tutorial_modules.html#modules-tutorial
	cat << EOF > ${spack_install_path}/etc/spack/modules.yaml
modules:
  enable:
    - tcl
  prefix_inspections:
    bin:
      - PATH
    man:
      - MANPATH
    share/man:
      - MANPATH
    share/aclocal:
      - ACLOCAL_PATH
    lib:
      - LIBRARY_PATH
    lib64:
      - LIBRARY_PATH
    include:
      - CPATH
    lib/pkgconfig:
      - PKG_CONFIG_PATH
    lib64/pkgconfig:
      - PKG_CONFIG_PATH
    share/pkgconfig:
      - PKG_CONFIG_PATH
    '':
      - CMAKE_PREFIX_PATH
  tcl:
    verbose: True
    hash_length: 0
    naming_scheme: '{name}/{version}-{compiler.name}-{compiler.version}'
    whitelist:
      - gcc
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
    #openmpi:
    #  environment:
    #    set:
    #      SLURM_MPI_TYPE: pmi2
    #      #OMPI_MCA_btl_openib_warn_default_gid_prefix: '0'
    netlib-scalapack:
      suffixes:
        '^openmpi': openmpi
        '^mpich': mpich
    ^python:
      autoload:  direct
  lmod:
    hierarchy:
      - mpi
EOF
    cat ${spack_install_path}/etc/spack/modules.yaml

    echo "OSUSER=${OSUSER}"
    echo "OSGROUP=${OSGROUP}"
	chown -R ${OSUSER}:${OSGROUP} ${spack_install_path}
    chmod -R go+rwX ${spack_install_path}

    #. /etc/profile.d/spack.sh
	su - ${OSUSER} -c ". /etc/profile && spack bootstrap"
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

