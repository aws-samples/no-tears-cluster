# Setup Cloud9, IAM, pcluster environment

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
