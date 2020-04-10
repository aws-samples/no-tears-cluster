# COVID-19 AWS HPC Cluster Deployment Guide

## Launch the COVID19 HPC QuickStart Environment

### Step 1
To deploy, click:

| Region       | Stack                                                                                                                                                                                                                                                                                                              |
|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| us-east-1    | [![amplifybutton](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?stackName=AWS-HPC-Quickstart&templateURL=https://covid19hpc-quickstart.s3.amazonaws.com/cfn.yaml)       |
| us-west-2    | [![amplifybutton](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?stackName=AWS-HPC-Quickstart&templateURL=https://covid19hpc-quickstart.s3.amazonaws.com/cfn.yaml)       |
| eu-west-1    | [![amplifybutton](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://eu-west-1.console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/create/review?stackName=AWS-HPC-Quickstart&templateURL=https://covid19hpc-quickstart.s3.amazonaws.com/cfn.yaml)       |
| eu-central-1 | [![amplifybutton](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://eu-central-1.console.aws.amazon.com/cloudformation/home?region=eu-central-1#/stacks/create/review?stackName=AWS-HPC-Quickstart&templateURL=https://covid19hpc-quickstart.s3.amazonaws.com/cfn.yaml) |

If you have not authenticated with the [AWS Management Console](https://signin.aws.amazon.com/console), you will be prompted to login with the AWS Account ID or alias, IAM user name, and password that was provided to you. 

### Step 2
After clicking `Launch Stack` you will be redirected to the CloudFormation **Quick create stack** screen. 

<img width="982" alt="Quick create stack" src="https://user-images.githubusercontent.com/187202/79027970-db4d4e00-7b53-11ea-89c1-7feba2029df9.png">

### Step 3

Scroll to the bottom of the page, and leave most of the Parameters as they are. 

1. Enter an initial `BudgetLimit` for the project. This will be used to track spending and send an alert when you cross 80%. 

2. Update `NotificationEmail` that will receive budget notifications. 

3. Fill out the `UserPasswordParameter` with a temporary password. Keep it simple! You will be prompted to change it on first use.

2. Select `I acknowledge that AWS Cloudformation might create IAM resources`. 

3. Now, click `Create Stack` to deploy the QuickStart Environment. 

<img width="982" alt="HPCQuickstartParameters" src="https://user-images.githubusercontent.com/187202/79084526-e80ba680-7cf9-11ea-905d-ba0db4033056.png">

### Deployment 
Deployment takes about 15 minutes. This QuickStart provisions: 
- a Cloud9 Integrated Development Environment (IDE) in the selected region;
- an AWS Parallel Cluster environment, named `covid-cluster`, for batch scheduled jobs and interactive computing;
- a non-root IAM User, with full Administrator access to the AWS Console to create custom architectures. 
- a Budget notification email at `80% of the BudgetLimit`

Provisioning is complete when all Stacks show *CREATE_COMPLETE*. 

![image](https://user-images.githubusercontent.com/187202/79025531-ab01b180-7b4b-11ea-8234-9bc393f69893.png)

--- 

## Onboarding Users

When all stacks show *CREATE_COMPLETE*, click on the `Outputs` tab of the `AWS-HPC-Quickstart` stack. Send the end-user the following information (3 of 4 are on the Outputs tab): 

1. `ResearchWorkspaceURL` -- URL to directly access the Cloud9 Research Environment. 

2. `UserLoginUrl` -- To authenticate into the AWS Console to create custom architectures. 

3. `UserName` -- The AWS IAM username for the end user. 

4. `Password` that you entered to launch the CloudFormation stack. 



Click on the value of `UserLoginUrl` and your web browser will be re-directed to an AWS Cloud9 interactive console:

<img width="849" alt="Outputs" src="https://user-images.githubusercontent.com/187202/79085211-3cfcec00-7cfd-11ea-94f9-8a8cf88e535b.png">

---
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

## Developer Setup

<details>
<summary>Click to expand</summary>
<br>
The first step is installing node.js, this can be done easily with Homebrew. After that completes, install aws-cdk:

```
$ brew install node
$ npm install -g aws-cdk
```
(Alternatively, use ```brew install aws-cdk```)

Create a python virtualenv or conda environment. We assume this is in ```./.env```. 

Now you can activate the python virtualenv and install the python dependencies:

```
$ source .env/bin/activate
$ pip install -r requirements.txt
```

At this point, it's time to setup CDK, the following needs to be done once in each account:

```
$ cdk bootstrap
```

And finally, deploy the app:

```
$ cdk deploy --parameters UserPasswordParameter=******* --parameters NotificationEmail=*******@amazon.com
```

I've surely missed a bunch of python dependencies, the format for installing those is:

```
$ pip install aws-cdk.custom-resources
```

Once it finishes deploy, you'll get an ouput with a link to the Cloud9 URL. Click on that to quickly see the Cloud9 result:

![image](https://user-images.githubusercontent.com/5545980/78568726-61c20280-77d7-11ea-84a5-bdf0d7a0cb95.png)

## Deploying to Public Bucket

Use the include `upload.sh` script to publish the template and assets (lambda zips, bootstrap scripts, etc.) in an S3 bucket. 

```bash
$ sh upload.sh [target-bucket-name]
```

This will create a modified `cfn.yaml` in the app directory. The script also creates buckets: 

- s3://`target-bucket-name`, the central repository for the template and assets

- s3://`target-bucket-name`-`region`, a clone of the central repository, where `region` expands to all AWS public regions.

Before publishing the template, the upload script synthesizes a yaml template and transforms the parameters and asset URLs to match the regional buckets. The final output, `cfn.yaml`, will reflect all changes. 

## Pro-Tips

Use `cdk synth | less` to see the generated template.

Provide parameters to the stack via `cdk deploy --parameters pcluster:KEY=VALUE`.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
</details>
