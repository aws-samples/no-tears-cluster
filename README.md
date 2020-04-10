# COVID-19 AWS HPC Cluster

## User Setup

To deploy, click:

| Region       | Stack                                                                                                                                                                                                                                                                                                              |
|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| us-east-1    | [![amplifybutton](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/template?stackName=AWS-HPC-Quickstart&templateURL=https://covid19hpc-quickstart.s3.amazonaws.com/cfn.yaml)       |
| us-west-2    | [![amplifybutton](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/template?stackName=AWS-HPC-Quickstart&templateURL=https://covid19hpc-quickstart.s3.amazonaws.com/cfn.yaml)       |
| eu-west-1    | [![amplifybutton](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://eu-west-1.console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/create/template?stackName=AWS-HPC-Quickstart&templateURL=https://covid19hpc-quickstart.s3.amazonaws.com/cfn.yaml)       |
| eu-central-1 | [![amplifybutton](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://eu-central-1.console.aws.amazon.com/cloudformation/home?region=eu-central-1#/stacks/create/template?stackName=AWS-HPC-Quickstart&templateURL=https://covid19hpc-quickstart.s3.amazonaws.com/cfn.yaml) |

### Step 1
After clicking "Launch Stack" you'll be redirected to a screen, leave everything as default and click "Next":

![image](https://user-images.githubusercontent.com/5545980/79008676-bbe20100-7b12-11ea-8f08-cd9b32415221.png)

### Step 2
Leave all the parameters as they are and click "Next":

![image](https://user-images.githubusercontent.com/5545980/79008772-f481da80-7b12-11ea-852d-66d6963ecfb4.png)

### Step 3
Click "Next":
![image](https://user-images.githubusercontent.com/5545980/79008829-10857c00-7b13-11ea-92ac-921eb6129eda.png)

### Step 4
Select "I acknowledge that AWS Cloudformation might create IAM resource" and click "Create Stack"
![image](https://user-images.githubusercontent.com/5545980/79008876-272bd300-7b13-11ea-9172-5d0ca9501038.png)

### Step 5
After the stack goes into CREATE_COMPLETE, click on the "Outputs" tab of the AWS-HPC-Quickstart stack, there you'll see a URL. Click on that URL and you'll be re-directed to the console:

![image](https://user-images.githubusercontent.com/5545980/79009644-d4ebb180-7b14-11ea-9029-e79d75647708.png)

## Developer Setup

<details>
<summary>Click to expand</summary>
<br>
The first step is installing node.js, this can be done easily with Homebrew. After that completes, install aws-cdk:

```
$ brew install node
$ npm install -g aws-cdk
```

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
$ cdk deploy
```

I've surely missed a bunch of python dependencies, the format for installing those is:

```
$ pip install aws-cdk.custom-resources
```

Once it finishes deploy, you'll get an ouput with a link to the Cloud9 URL. Click on that to quickly see the Cloud9 result:

![image](https://user-images.githubusercontent.com/5545980/78568726-61c20280-77d7-11ea-84a5-bdf0d7a0cb95.png)

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
