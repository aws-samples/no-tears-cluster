USER_GUIDE.md
# COVID-19 AWS HPC Cluster User Guide

## 0. Prerequisites

* A computer with an internet connection running Microsoft Windows, Mac OS X, or Linux.
* An internet browser such as Chrome, Firefox, or Safari.
* Familiarity with common Linux commands.

## 1. Get Your Credentials

Your AWS partner will stand up a research environment for you. They will issue you the following: 

1. `UserLoginUrl` -- a URL to authenticate into the AWS Console. 

2. `UserName` -- the AWS IAM username for the end user. 

3. `Password` -- an initial password. You are required to reset this on first login. 

4. `ResearchWorkspaceURL` -- a URL to directly access your Cloud9 Research Workspace (details below). 

## 2. Sign in to the AWS Console
Navigate your browser to the `UserLoginUrl` and authenticate into the AWS Management Console. 

Use `UserName` for **IAM user name**, and the `Password` that was provided to you. Do not change the value of the **Account ID**. 

<img width="983" alt="AWS Console Sign-In" src="https://user-images.githubusercontent.com/187202/79087670-a4b73500-7d05-11ea-9128-053d45b490fd.png">

### First Login
<details>
<summary>Click to expand</summary>
<br>
On first login, you will be forced to change your password: 

<img width="983" alt="ChangePassword" src="https://user-images.githubusercontent.com/187202/79088937-d7fbc300-7d09-11ea-8f5d-9a9cfa8f29c0.png">

</details>

### The AWS Console
After you sign in, take a few minutes to explore the navigation components of the AWS Management Console.

* A search bar allows you to quickly locate services based on text.
* Recently visited services are located below the search bar.
* In the toolbar, the Services drop-down menu populates a list of all services.
* The Support drop-down menu includes links to support and [documentation](https://docs.aws.amazon.com/).
* The Region drop-down menu allows you to select a specific AWS Region.

![aws-console](https://user-images.githubusercontent.com/187202/79024890-e4d1b880-7b49-11ea-86f1-22e0bdd96ee1.png)

You are now ready to access the HPC Environment.

## 3. Get Started with the Research Workspace IDE

Navigate to your `ResearchWorkspaceUrl` and your web browser will be re-directed to an AWS Cloud9 interactive console like this:

![Cloud9](https://user-images.githubusercontent.com/187202/79025821-81955580-7b4c-11ea-9f2f-3fd128afe939.png)

Cloud9 is a powerful Integrated Development Environment where you can write, run, and debug code via your browser. Cloud9 provides the software and tooling needed for dynamic programming languages including JavaScript, Python, PHP, Ruby, Go, and C++. Visit the [AWS Cloud9 Features page](https://aws.amazon.com/cloud9/details/) for more informatiom. 


### Bash Terminal

While inside Cloud9, we assume you will use the ```bash``` terminal (at the bottom of the screen) for most of your HPC work. 

💡ProTip: Click the  <img width="31" alt="maximizeBashIcon" src="https://user-images.githubusercontent.com/187202/79088606-b817cf80-7d08-11ea-8624-f04ddaf924dc.png"> icon to maximize the terminal window. 

Use the Cloud9 BASH console to confirm that the AWS Parallel Cluster Tool (`pcluster`) and AWS CLI (`aws`) are available. 

```bash
which pcluster
which aws
```

The `pcluster` command will help you connect to and reconfigure a scalable, on-demand HPC environment. The `aws` command enables interaction with other AWS services, like putting data into S3 Object Storage.

The Cloud9 environment comes preloaded with AWS Parallel Cluster configurations for Tightly-Coupled and Loosely-Coupled (a.k.a. Distributed) jobs. Feel free to customize the cluster configurations, including your choice of Scheduler, following the [Parallel Cluster User Guide](https://docs.aws.amazon.com/parallelcluster/latest/ug/aws-parallelcluster-ug.pdf). 

## 4. Connect to the HPC Environment
Confirm the name of your AWS Parallel Cluster: 
```
pcluster list
```
The name should be `covid-cluster` and the state should be `CREATE_COMPLETE`. 
<img width="434" alt="Screen Shot 2020-04-12 at 10 16 55 PM" src="https://user-images.githubusercontent.com/187202/79089316-59078a00-7d0b-11ea-9695-c39c50b95b6f.png">

Connect to the cluster: 
```bash
pcluster ssh covid-cluster
```
<img width="607" alt="Screen Shot 2020-04-12 at 10 23 51 PM" src="https://user-images.githubusercontent.com/187202/79089604-55283780-7d0c-11ea-9709-e5a6a091ff73.png">

- 💡ProTip: You can also Remote Desktop into `covid-cluster` (for Visualization)
    <details>
    <summary>Click to expand</summary>
    <br>

    Instead of `pcluster ssh`, use this command: 

    ```bash
    pcluster dcv connect covid-cluster
    ```

    <img width="984" alt="Screen Shot 2020-04-13 at 1 41 06 AM" src="https://user-images.githubusercontent.com/187202/79098944-aa724200-7d28-11ea-897c-10e0174dedf1.png">

    Open the DCV URL for in another browser tab, and proceed through the warning about an Invalid Cert Authority. You will get access to a full Ubuntu Desktop: 
    
    <img width="984" alt="Screen Shot 2020-04-13 at 1 41 36 AM" src="https://user-images.githubusercontent.com/187202/79099935-d8588600-7d2a-11ea-9935-3f5c6cabca5d.png">

    <img width="984" alt="Screen Shot 2020-04-13 at 1 56 40 AM" src="https://user-images.githubusercontent.com/187202/79099564-0b4e4a00-7d2a-11ea-8003-40747e7f6990.png">

    </details>


## The `covid-cluster` HPC Environment

The `covid-cluster` HPC Environment has the following features: 

- [Ubuntu 18.04](https://ubuntu.com/aws) operating system (`apt`),
- [SLURM](https://slurm.schedmd.com/documentation.html) Workload Manager (`sbatch`, `srun`, `squeue`, `sinfo`),
- [Environment Modules](http://modules.sourceforge.net/) (`module avail`),
- [Spack](https://spack.io/) Package Manager (`spack`),
- [FSx Lustre](https://aws.amazon.com/fsx/lustre/) scratch filesystem (`/scratch`),
- A Master node for job scheduling, interactive development, and
- Multiple Compute nodes that scale up from 0 based on the jobs you submit. 

### Master and Compute Nodes

The default `covid-cluster` configuration is described in the table below. These values will vary by project, so consult your AWS partner for specific cluster information. 

| | # Nodes | Longevity | Instance Type | EFA |  <ul>Purpose</ul>  |
|---|---|---|---|---|---| 
|  Master  |  1 | persistent |  c5n.2xlarge  |  No  | <ul><li>Job Submission</li></ul><ul><li>Interactive Analysis and Development</li></ul><ul><li>Visualization</li></ul> |
| Compute |  0 - 10 | auto-scaling |  c5n.18xlarge | Yes |  <ul><li>Batch Processing</li></ul><ul><li>Tightly or Loosely Coupled Job Processing</li></ul>
| | | | |


### Filesystem Shares
The `covid-cluster` Master and Compute nodes share a number of common filesystems as described in the table below. Leverage shared filesystems to reduce data movement and duplication. 

| Path  |  Recommended Use |  Storage Backend |  Size  |
|---|---|---|---|
| /home  |   |  EBS (gp2) | 200 GB |  
| /shared | Application source code, compiled binaries, user-space software and job scripts  |  EBS (gp2) | 500 GB  |  
| /scratch | Reference data and intermediate output from jobs  | FSx Lustre (SCRATCH2) | 1.2 TB |   |
| /opt/slurm | Do NOT write to this path  |  - |  - |  
| /opt/intel | Do NOT write to this path  |  - | - |  
| s3://aws-hpc-quickstart-datarepository****** | Input files and final output files. <br>💡Note: this bucket is not directly mounted, but instances do have read/write access via the `aws s3` command  | S3 | N/A |  

To identify mounted filesystems and the available storage on the cluster:

```bash
showmount -e localhost
df -h
```
<img width="582" alt="Screen Shot 2020-04-12 at 11 35 29 PM" src="https://user-images.githubusercontent.com/187202/79092378-53637180-7d16-11ea-81fd-a102d33bc87f.png">


### Accessing Data

COVID19 data can be **pulled** into the `covid-cluster` on either Master or Compute nodes. 

For example, to download a subset of data from the [AWS COVID19 Data Lake](https://aws.amazon.com/blogs/big-data/a-public-data-lake-for-analysis-of-covid-19-data/), it might look something like: 

```bash
aws s3 ls s3://covid19-lake
aws s3 sync s3://covid19-lake/static-datasets /scratch/.
```
<img width="984" alt="Screen Shot 2020-04-12 at 11 57 33 PM" src="https://user-images.githubusercontent.com/187202/79093617-6e37e500-7d1a-11ea-8715-84be8b606262.png">

Additional COVID19 related datasets are available on the [AWS Data-Exchange](https://aws.amazon.com/data-exchange/covid-19/).

The HPC Environment also has tools to **pull** data from the Internet (e.g., `scp`, `ftp`, `wget`, etc. from the `covid-cluster` Master node). Direct connections from the Internet (i.e., your home workstation) to the HPC environment are restricted. 

If pulling the data is not an option, then you can push data into `covid-cluster` via an S3 Bucket as intermediary. Your HPC Environment has an S3 bucket ready to use named something like `s3://aws-hpc-quickstart-datarepositoryXXXXXXX-XXXXXXXXX`, where XXXXXXX-XXXXXXXXX is specific to your environment. Run ```aws s3 ls``` within the `covid-cluster` environment to identify your bucket name. 

For help installing and activating the AWS CLI in your own environment, see [this guide](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html). You will also need to [create an Access key-pair](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html) for the CLI.  

Copy a folder from your home environment into S3 storage 
```bash
aws s3 sync input_dir s3://mybucket-012345/input_dir
```
Get the folder from S3 storage on the Master node
```
aws s3 sync s3://mybucket-012345/input_dir /scratch/input_dir
```



### Install Software
The `ubuntu` user has full permissions to install software in the HPC environment via the `sudo` command. Note, however, in order to use software in a batch scheduled job, you must either:  
1. install the software on a shared filesystem common to Master and Compute nodes, or
2. install the software individually on every compute node. 

We strongly recommend 1. To this end, we provide `/shared` as a shared file system common to Master and Compute nodes. Furthermore, we have pre-loaded the `spack` package manager in your environment to simplify installation of packages. `spack` optimizes software installs for HPC environments, and will  install packages to `/shared/spack`. Software installed with `spack` is also immediately available as a `module`. 

For example, to install `SRA-Toolkit`, you might use the following workflow to search for, and then install the package: 
```bash
spack list sra
spack install sra-toolkit
```
<img width="984" alt="Screen Shot 2020-04-12 at 10 43 47 PM" src="https://user-images.githubusercontent.com/187202/79090384-1ba4fb80-7d0f-11ea-9e79-a5251ee2d454.png">



### Load Environment

To see all available modules (including those installed by `spack`), and then load a package, use this syntax: 

```bash
module avail
module load intelmpi
```
<img width="984" alt="Screen Shot 2020-04-13 at 2 07 17 AM" src="https://user-images.githubusercontent.com/187202/79100229-a09e0e00-7d2b-11ea-9775-3b0ab8a4e522.png">

Review loaded modules and get details of how a module impacts your environment: 

```bash
module list
module show intelmpi
```
<img width="984" alt="Screen Shot 2020-04-13 at 2 07 58 AM" src="https://user-images.githubusercontent.com/187202/79100224-9ed44a80-7d2b-11ea-924d-6de9f860e1b9.png">

For examples of how to leverage the AWS provided intelmpi and openmpi modules with EFA support, see AWS Blogs like [this](
https://aws.amazon.com/blogs/compute/running-ansys-fluent-on-amazon-ec2-c5n-with-elastic-fabric-adapter-efa/)
and 
[this](https://aws.amazon.com/blogs/opensource/scale-hpc-workloads-elastic-fabric-adapter-and-aws-parallelcluster/). 

### Submit Jobs

AWS Parallel Cluster integrates the [SLURM](https://slurm.schedmd.com/documentation.html) job scheduler and Auto-Scaling to meet the demand of your job queue. By default, clusters scale from 0, up to a maximum of 10 Compute nodes. The Master (login) node persists regardless of the scale of the Compute nodes.

- Get the current list of nodes: 

    ```bash 
    sinfo -a
    ```

- An example SLURM job script: 
    <details>
    <summary>test_job.sbatch (Click to Expand) </summary>
    <br>

    ```bash
    #!/bin/bash
    #SBATCH --nodes=2
    #SBATCH --ntasks-per-node=1
    #SBATCH --cpus-per-task=4
    module purge 
    module load intelmpi sra-toolkit
    module list

    env
    sleep 60

    which fasterq-dump
    ```
    </details>
    
- Submit a test job:

    ```bash
    sbatch /scratch/test_job.sbatch
    ```
    <img width="495" alt="Screen Shot 2020-04-13 at 8 42 16 AM" src="https://user-images.githubusercontent.com/187202/79125099-2e492000-7d63-11ea-81f2-3ccadf3a7e6c.png">

- Check the status of a job:
    ```bash
    squeue
    ```
    💡ProTip: when the queue has been idle a while, the Compute nodes will scale-in (terminate). Jobs will be held in the queue until new Compute nodes are spun up. 
    <img width="984" alt="Screen Shot 2020-04-13 at 8 43 46 AM" src="https://user-images.githubusercontent.com/187202/79125096-2d17f300-7d63-11ea-8432-bc101d6d95b7.png">

    When compute nodes become available, `squeue` will look like: 
    <img width="984" alt="Screen Shot 2020-04-13 at 8 48 39 AM" src="https://user-images.githubusercontent.com/187202/79125416-c3e4af80-7d63-11ea-8253-2b391ddcf821.png">

- Completed Jobs
When jobs complete, they are removed from `squeue`. Find out which jobs have finished with: 

    ```bash
    squeue
    sacct
    ```
    <img width="624" alt="Screen Shot 2020-04-13 at 8 52 39 AM" src="https://user-images.githubusercontent.com/187202/79125671-263db000-7d64-11ea-9e45-cd67760a7e76.png">

    💡ProTip: You can also view detailed information about the job with
    ```bash
    scontrol show job [JobID]
    ```
    <img width="624" alt="Screen Shot 2020-04-13 at 8 51 16 AM" src="https://user-images.githubusercontent.com/187202/79125562-03130080-7d64-11ea-9e37-df20ffc8d034.png">



## FAQ

- If you see the following:
**The security token included in the request is invalid**

    It's likely an issue with the account having been just created. Wait for some time and try again. 

- On first login to the Cloud9 terminal you may see something like:
    ```
    Agent pid 3303
    Identity added: /home/ec2-user/.ssh/AWS-HPC-Quickstart-NJCH9esX (/home/ec2-user/.ssh/AWS-HPC-Quickstart-NJCH9esX)
    ```
    Ignore these messages. They indicate that your SSH key for Parallel Cluster was located.