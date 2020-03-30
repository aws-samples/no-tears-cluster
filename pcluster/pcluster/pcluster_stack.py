from aws_cdk import (
    aws_s3 as s3,
    aws_cloud9 as cloud9,
    aws_ec2 as ec2,
    aws_cloudtrail as cloudtrail,
    aws_ssm as ssm,
    core
)

class PclusterStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

	    # create a VPC
        vpc = ec2.Vpc(self, 'VPC', cidr='10.0.0.0/16')

        # create a private and public subnet per vpc
        selection = vpc.select_subnets(
            subnet_type=ec2.SubnetType.PRIVATE
        )

        # Create a Bucket
        bucket = s3.Bucket(self, "DataRepository")

        # Setup CloudTrail
        cloudtrail.Trail(self, 'CloudTrail', bucket=bucket)

        # Create a Cloud9 instance
        cloud9_instance = cloud9.Ec2Environment(self, 'Cloud9Env', vpc=vpc)
        core.CfnOutput(self, 'URL',  value=cloud9_instance.ide_url )
