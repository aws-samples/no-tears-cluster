# Covid-19 Rapid Cluster

This repo rapidly deploys a cloudformation stack that creates a Cloud9 instance, VPC, subnets, IAM roles ect.

To get started, run:

```bash
cd pcluster/
cdk deploy
```

Then visit the EC2 Console to connect to the machine.

Once connected, run:

```bash
git clone https://github.com/sean-smith/covid19hpc
cd covid19hpc/
./bootstrap.sh
```

That's it!
