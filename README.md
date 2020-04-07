# Covid-19 Rapid Cluster

This repo rapidly deploys a cloudformation stack that creates a Cloud9 instance, VPC, subnets, IAM roles ect.

To get started, run:

```bash
cd quickstart/
```

That's it!

## Accout  independent Version
To build an account independent version use ./upload.sh This will upload all assets to $s3_bucket and make sure all references in cfn.yaml point to the correct resources
