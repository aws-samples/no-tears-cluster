# Cloud9 COVID-19 Rapid Cluster

To get started, clone this repo locally:

```bash
git clone https://github.com/sean-smith/covid19hpc
cd covid19hpc/
```

### Customer Workflow

Go to [CloudFormation Console](https://console.aws.amazon.com/cloudformation/home) > Create Stack > With new resources (standard)

Fill in the following options:

```bash
Template is Ready
Stack Name: pcluster
Upload a template file
```

Select the template `templates/cloud9-ide-master.template.yaml` (TODO change this to S3 URL)

Then click `Next`.

For parameters, select 2 AZ's where you want to deploy to, then create the stack.

### Development Testing

Edit the Makefile to put in your bucket and region:

```bash
s3_bucket=seaam
region=us-east-1
```

Edit the parameters, 

Then create it:

```bash
make create
```
