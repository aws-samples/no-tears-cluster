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
accounting_log_path=${4:-/opt/slurm/log}
accounting_log_file=${5:-sacct.log}

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
        OPENMPI_VERSION=$(. /etc/profile && module avail openmpi 2>&1 | grep openmpi | head -n 1 | cut -d / -f 2)
        # e.g., INTELMPI_VERSION=2019.7.166
        INTELMPI_VERSION=$(. /etc/profile && module show intelmpi 2>&1 | grep I_MPI_ROOT | sed 's/[[:alpha:]|_|:|\/|(|[:space:]]//g' | awk -F- '{print $1}' )
        # e.g., SLURM_VERSION=19.05.5
        SLURM_VERSION=$(. /etc/profile && sinfo --version | cut -d' ' -f 2)
        # e.g., LIBFABRIC_VERSION=1.10.0
        # e.g., LIBFABRIC_MODULE=1.10.0amzn1.1
        LIBFABRIC_MODULE=$(. /etc/profile && module avail libfabric 2>&1 | grep libfabric | head -n 1 )
        LIBFABRIC_MODULE_VERSION=$(. /etc/profile && module avail libfabric 2>&1 | grep libfabric | head -n 1 |  cut -d / -f 2 )
        LIBFABRIC_VERSION=${LIBFABRIC_MODULE_VERSION//amzn*}
        # e.g., GCC_VERSION=7.3.5
        GCC_VERSION=$( gcc -v 2>&1 |tail -n 1| awk '{print $3}' )

        #NOTE: as of parallelcluster v2.8.0, SLURM is built with PMI3
        cat << EOF > ${spack_install_path}/etc/spack/packages.yaml
packages:
  binutils:
    variants: +gold+headers+libiberty~nls
    version:
      - 2.33.1
  openfoam:
    version:
      - 2006
  paraview:
    variants: +qt+python3
  qt:
    variants: +opengl
  ncurses:
    variants: +termlib
  sqlite:
    variants: +column_metadata
  hdf5:
    variants: +hl
  mesa:
    # Will not work for graviton2; need a newer version of mesa for ARM
    variants: swr=avx,avx2
    version:
      - 18.3.6
  llvm:
    version:
      - 6.0.1
  hwloc:
    version:
      - 1.11.11
  munge:
    # Refer to ParallelCluster global munge space
    variants: localstatedir=/var
  openmpi:
    buildable: true
    variants: fabrics=ofi +pmi +legacylaunchers schedulers=slurm
    version: [4.1.0,4.0.3]
    externals:
    - spec: openmpi@${OPENMPI_VERSION}  fabrics=ofi +pmi +legacylaunchers schedulers=slurm
      modules:
      - openmpi/${OPENMPI_VERSION}
  intel-mpi:
    buildable: true
    version: [2020.2.254]
    externals:
    - spec: intel-mpi@${INTELMPI_VERSION}
      modules:
      - intelmpi
  slurm:
    buildable: false
    variants: +pmix sysconfdir=/opt/slurm/etc
    version: [20-02-4-1,19-05-5-1]
    externals:
    - spec: slurm@${SLURM_VERSION} +pmix sysconfdir=/opt/slurm/etc
      prefix: /opt/slurm/
  libfabric:
    buildable: true
    variants: fabrics=efa,tcp,udp,sockets,verbs,shm,mrail,rxd,rxm
    version: [1.11.1,1.9.1]
    externals:
    - spec: libfabric@${LIBFABRIC_VERSION} fabrics=efa,tcp,udp,sockets,verbs,shm,mrail,rxd,rxm
      modules:
      - libfabric-aws/${LIBFABRIC_MODULE}
  mpich:
    # For EFA (requires ch4)
    variants: ~wrapperrpath pmi=pmi netmod=ofi device=ch4
  all:
    providers:
      blas:
      - openblas
      mpi:
      - openmpi
      - mpich
    variants: +mpi
    permissions:
      read: world
      write: user
EOF

    cat ${spack_install_path}/etc/spack/packages.yaml

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
    hash_length: 6
    projections:
      all: '{name}/{version}-{compiler.name}-{compiler.version}'
      ^libfabric: '{name}/{version}-{^mpi.name}-{^mpi.version}-{^libfabric.name}-{^libfabric.version}-{compiler.name}-{compiler.version}'
      ^mpi: '{name}/{version}-{^mpi.name}-{^mpi.version}-{compiler.name}-{compiler.version}'
    whitelist:
      - gcc
    blacklist:
      - slurm
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
      autoload:  direct
    gcc:
      environment:
        set:
          CC: gcc
          CXX: g++
          FC: gfortran
          F90: gfortran
          F77: gfortran
    openmpi:
      environment:
        set:
          SLURM_MPI_TYPE: "pmix"
          OMPI_MCA_btl_tcp_if_exclude: "lo,docker0,virbr0"
    miniconda3:
      environment:
        set:
          CONDA_PKGS_DIRS: ~/.conda/pkgs
          CONDA_ENVS_PATH: ~/.conda/envs
  lmod:
    hierarchy:
      - mpi
EOF
    cat ${spack_install_path}/etc/spack/modules.yaml

	cat << EOF >> ${spack_install_path}/etc/spack/mirrors.yaml
mirrors: { "aws-optimized": "s3://spack-mirrors/amzn2-e4s" }
EOF
    cat ${spack_install_path}/etc/spack/mirrors.yaml

    mkdir -p ${spack_install_path}/var/spack/environments/aws
	cat << EOF > ${spack_install_path}/var/spack/environments/aws/spack.yaml
spack:
  view: false
  concretization: separately

  mirrors: { "mirror": "s3://spack-mirrors/amzn2-e4s" }

  packages:
    all:
      providers:
        blas:
        - openblas
        mpi:
        - openmpi
        - mpich
      variants: +mpi
    binutils:
      variants: +gold+headers+libiberty~nls
      version:
        - 2.33.1
    openfoam:
      version:
        - 2006
    paraview:
      variants: +qt+python3
    qt:
      variants: +opengl
    ncurses:
      variants: +termlib
    sqlite:
      variants: +column_metadata
    hdf5:
      variants: +hl
    mesa:
      # Will not work for graviton2; need a newer version of mesa for ARM
      variants: swr=avx,avx2
      version:
        - 18.3.6
    llvm:
      version:
        - 6.0.1
    hwloc:
      version: [2.4.0]
    munge:
      # Refer to ParallelCluster global munge space
      variants: localstatedir=/var
    openmpi:
      variants: fabrics=ofi +pmi +legacylaunchers schedulers=slurm
      version: [4.1.0,4.0.3]
    intel-mpi:
      version: [2020.2.254]
    slurm:
      variants: +pmix sysconfdir=/opt/slurm/etc
      version: [20-02-4-1,19-05-5-1]
    libfabric:
      variants: fabrics=efa,tcp,udp,sockets,verbs,shm,mrail,rxd,rxm
      version: [1.11.1,1.9.1]
    mpich:
      # For EFA (requires ch4)
      variants: ~wrapperrpath pmi=pmi netmod=ofi device=ch4
    libevent:
        version: [2.1.8]

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
      hash_length: 6
      projections:
        all: '{name}/{version}-{compiler.name}-{compiler.version}'
        ^libfabric: '{name}/{version}-{^mpi.name}-{^mpi.version}-{^libfabric.name}-{^libfabric.version}-{compiler.name}-{compiler.version}'
        ^mpi: '{name}/{version}-{^mpi.name}-{^mpi.version}-{compiler.name}-{compiler.version}'
      whitelist:
        - gcc
      blacklist:
        - slurm
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
        autoload:  direct
      gcc:
        environment:
          set:
            CC: gcc
            CXX: g++
            FC: gfortran
            F90: gfortran
            F77: gfortran
      openmpi:
        environment:
          set:
            SLURM_MPI_TYPE: "pmix"
            OMPI_MCA_btl_tcp_if_exclude: "lo,docker0,virbr0"
      miniconda3:
        environment:
          set:
            CONDA_PKGS_DIRS: ~/.conda/pkgs
            CONDA_ENVS_PATH: ~/.conda/envs
    lmod:
      hierarchy:
        - mpi
EOF
	cat ${spack_install_path}/var/spack/environments/aws/spack.yaml

    echo "OSUSER=${OSUSER}"
    echo "OSGROUP=${OSGROUP}"
	chown -R ${OSUSER}:${OSGROUP} ${spack_install_path}
    chmod -R go+rwX ${spack_install_path}

    #. /etc/profile.d/spack.sh
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

