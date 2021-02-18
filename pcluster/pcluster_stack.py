# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_fsx as fsx,
    aws_s3 as s3,
    aws_s3_assets as assets,
    aws_cloud9 as cloud9,
    aws_ec2 as ec2,
    aws_cloudtrail as cloudtrail,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_cloudformation as cfn,
    aws_secretsmanager as secretsmanager,
    aws_budgets as budgets,
    custom_resources as cr,
    core as cdk,
    region_info
)
import json
from pcluster import __version__

# Returns package version numbers available from pypi
def get_version_list(package_name):
    import json
    import requests
    from distutils.version import StrictVersion

    url = "https://pypi.org/pypi/%s/json" % (package_name,)
    data = requests.get(url).json()
    versions = data["releases"].keys()
    return list(versions)

# Requires that you export GIT_AUTH_TOKEN before running CDK.
def get_git_version_list(git_owner, package_name):
    import json
    import os
    from github import Github

    g = Github(os.environ.get('GIT_AUTH_TOKEN'))

    versions = [v.tag_name for v in g.get_repo(f"{git_owner}/{package_name}").get_releases()]
    return list(versions)

class PclusterStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Version of ParallelCluster for Cloud9.
        pcluster_version = cdk.CfnParameter(self, 'ParallelClusterVersion', description='Specify a custom parallelcluster version. See https://pypi.org/project/aws-parallelcluster/#history for options.', default='2.10.1', type='String', allowed_values=get_version_list('aws-parallelcluster'))

        # S3 URI for Config file
        config = cdk.CfnParameter(self, 'ConfigS3URI', description='Set a custom parallelcluster config file.', default='https://notearshpc-quickstart.s3.amazonaws.com/{0}/config.ini'.format(__version__))

        #spack_version = cdk.CfnParameter(self, 'SpackVersion', description='Specify a custom Spack version. See https://github.com/spack/spack/releases for options.', default='v0.16.0', type='String', allowed_values=get_git_version_list('spack','spack'))
        spack_versions = ['develop']
        spack_versions.extend(get_git_version_list('spack','spack'))
        spack_version = cdk.CfnParameter(self, 'SpackVersion', description='Specify a custom Spack version. See https://github.com/spack/spack/releases for options.', default='v0.16.0', type='String', allowed_values=spack_versions)

        spack_config_uri = cdk.CfnParameter(self, 'SpackConfigS3URI', description='Set a custom Spack Config (i.e. S3URI or HTTPSURL to prefix containing packages.yaml, modules.yaml, mirrors.yaml, etc.). Do not include trailing \'/\' on URI.', default='https://notearshpc-quickstart.s3.amazonaws.com/{0}/spack'.format(__version__))

        # Password
        password = cdk.CfnParameter(self, 'UserPasswordParameter', default='Ch4ng3M3!', description='Set a password for the hpc-quickstart user (Default: \'Ch4ng3M3!\')', no_echo=True)

        # create a VPC
        vpc = ec2.Vpc(self, 'VPC', cidr='10.0.0.0/16',
                      gateway_endpoints={
                          "S3": ec2.GatewayVpcEndpointOptions(
                              service=ec2.GatewayVpcEndpointAwsService.S3
                          ),
                          "DynamoDB": ec2.GatewayVpcEndpointOptions(
                              service=ec2.GatewayVpcEndpointAwsService.DYNAMODB
                          )
                      },
                      max_azs=99)

        # create a private and public subnet per vpc
        selection = vpc.select_subnets(
            subnet_type=ec2.SubnetType.PRIVATE
        )

        # Output created subnets
        for i, public_subnet in enumerate(vpc.public_subnets):
            cdk.CfnOutput(self, 'PublicSubnet%i' % i,  value=public_subnet.subnet_id)

        for i, private_subnet in enumerate(vpc.private_subnets):
            cdk.CfnOutput(self, 'PrivateSubnet%i' % i,  value=private_subnet.subnet_id)

        cdk.CfnOutput(self, 'VPCId',  value=vpc.vpc_id)

        create_lustre = cdk.CfnParameter(self, 'EnableFSxLustre', type="String", description='Enable/Disable FSx Lustre creation.', default='true', allowed_values=['true', 'false'])
        fsx_condition = cdk.CfnCondition(self, "FSxLustreCondition", expression=cdk.Fn.condition_equals(create_lustre, 'true'))

        fsxlustre_sg = ec2.SecurityGroup(self, 'FSxLustreSecurityGroup', vpc=vpc, allow_all_outbound=True, description='Allow Cross Traffic from VPC to Lustre')

        pcluster_sg = ec2.SecurityGroup(self, 'PClusterSecurityGroupForLustre', vpc=vpc, allow_all_outbound=False, description='Allow Cross Traffic from VPC to Lustre')
        pcluster_sg.add_ingress_rule(pcluster_sg, ec2.Port.tcp(988), description='Allows Lustre traffic between Lustre clients')
        pcluster_sg.add_ingress_rule(fsxlustre_sg, ec2.Port.tcp(988), description='Allows Lustre traffic between Amazon FSx for Lustre file servers and Lustre clients')
        pcluster_sg.add_ingress_rule(pcluster_sg, ec2.Port.tcp_range(1021, 1023), description='Allows Lustre traffic between Amazon FSx for Lustre file servers')
        pcluster_sg.add_ingress_rule(fsxlustre_sg, ec2.Port.tcp_range(1021, 1023), description='Allows Lustre traffic between Amazon FSx for Lustre file servers and Lustre clients')

        pcluster_sg.add_egress_rule(pcluster_sg, ec2.Port.tcp(988), description='Allow Lustre traffic between Amazon FSx for Lustre file servers')
        pcluster_sg.add_egress_rule(fsxlustre_sg, ec2.Port.tcp(988), description='Allow Lustre traffic between Amazon FSx for Lustre file servers and Lustre clients')
        pcluster_sg.add_egress_rule(pcluster_sg, ec2.Port.tcp_range(1021, 1023), description='Allows Lustre traffic between Amazon FSx for Lustre file servers')
        pcluster_sg.add_egress_rule(fsxlustre_sg, ec2.Port.tcp_range(1021, 1023), description='Allows Lustre traffic between Amazon FSx for Lustre file servers and Lustre clients')

        # Create a Bucket
        data_bucket = s3.Bucket(self, "DataRepository")
        cdk.CfnOutput(self, 'DataRespository',  value=data_bucket.bucket_name)
        cloudtrail_bucket = s3.Bucket(self, "CloudTrailLogs")
        quickstart_bucket = s3.Bucket.from_bucket_name(self, 'QuickStartBucket', 'aws-quickstart')

        lustre_performance = cdk.CfnParameter(self, 'FSxLustrePerformance', description='The amount of read and write throughput for each 1 tebibyte of storage, in MB/s/TiB.', default=100, allowed_values=['12','40','50','100','200'], type='Number')
        lustre_type = cdk.CfnParameter(self, 'FSxLustreType', description='Sets the storage deployment type. Persistent file systems are designed for longer-term storage and workloads. The file servers are highly available and data is automatically replicated within the same Availability Zone (AZ) that is associated with the file system. Scratch file systems are designed for temporary storage and shorter-term processing of data. Data is not replicated and doesn\'t persist if a file server fails.', default='PERSISTENT_1', allowed_values=['PERSISTENT_1', 'SCRATCH_2'], type='String')
        lustre_import_policy = cdk.CfnParameter(self, 'FSxLustreImportPolicy', description='NONE - AutoImport is off. NEW - AutoImport is on, but only new objects in S3 will be imported. NEW_CHANGED - AutoImport is on, and any new objects and changes to existing objects will be imported.', default='NEW_CHANGED', allowed_values=['NEW_CHANGED', 'NEW', 'NONE'], type='String')
        lustre_storage_type = cdk.CfnParameter(self, 'FSxLustreStorageType', description='Sets the storage type for the file system you are creating. Valid values are SSD and HDD.', default='SSD', allowed_values=['SSD', 'HDD'])
        lustre_drive_cache = cdk.CfnParameter(self, 'FSxLustreDriveCacheType', description='This parameter is required when storage type is HDD. Set to READ to enable SSD Drive Cache Tier and improve the performance for frequently accessed files and allows 20% of the total storage capacity of the file system to be cached. Disabled whenever storage type is SSD. \'READ\' enables on HDD type.', allowed_values=['NONE','READ'], default='NONE')
        lustre_type_is_ssd = cdk.CfnCondition(self, "LustreTypeIsSSD", expression=cdk.Fn.condition_equals(lustre_storage_type.value_as_string, "SSD"))
        lustre_storage_capacity = cdk.CfnParameter(self, 'FSxLustreStorageCapacity', description='FSx Lustre filesystem capacity (in GiB). Scratch and persistent SSD-based file systems can be created in sizes of 1200 GiB or in increments of 2400 GiB. Persistent HDD-based file systems with 12 MB/s and 40 MB/s of throughput per TiB can be created in increments of 6000 GiB and 1800 GiB, respectively.', default=1200, type='Number')


        fsx_lustre_config = {
            "autoImportPolicy": lustre_import_policy.value_as_string,
            "deploymentType": lustre_type.value_as_string,
            "exportPath": 's3://%s' % ( data_bucket.bucket_name ),
            "importPath": 's3://%s' % ( data_bucket.bucket_name ),
            "perUnitStorageThroughput": lustre_performance.value_as_number,
            #"driveCacheType": cdk.Fn.condition_if(drive_cache_is_none.logical_id, cdk.Aws.NO_VALUE, lustre_drive_cache.value_as_string),
        }
        fsx_lustre_filesystem = fsx.CfnFileSystem(self, 'FSxLustreFileSystem',
                                                  file_system_type='LUSTRE', subnet_ids=[vpc.private_subnets[0].subnet_id],
                                                  lustre_configuration=fsx_lustre_config, security_group_ids=[fsxlustre_sg.security_group_id, pcluster_sg.security_group_id],
                                                  storage_capacity=lustre_storage_capacity.value_as_number, storage_type=lustre_storage_type.value_as_string)
        fsx_lustre_filesystem.add_override(
            "Properties.LustreConfiguration.DriveCacheType",
            {
                "Fn::If": [
                    lustre_type_is_ssd.logical_id,
                    cdk.Aws.NO_VALUE,
                    lustre_drive_cache.value_as_string
                ]
            }
        )
        fsx_lustre_filesystem.cfn_options.condition=fsx_condition
        cdk.CfnOutput(self, 'FSxID',  value=fsx_lustre_filesystem.ref, condition=fsx_condition)


        # Upload Bootstrap Script to that bucket
        bootstrap_script = assets.Asset(self, 'BootstrapScript',
            path='scripts/bootstrap.sh'
        )

        # Upload parallel cluster post_install_script to that bucket
        pcluster_post_install_script = assets.Asset(self, 'PclusterPostInstallScript',
            path='scripts/post_install_script.sh'
        )

        # Upload parallel cluster post_install_script to that bucket
        pcluster_config_script = assets.Asset(self, 'PclusterConfigScript',
            path='scripts/config.ini'
        )

        # Setup CloudTrail
        cloudtrail.Trail(self, 'CloudTrail', bucket=cloudtrail_bucket)

        # Create a Cloud9 instance
        # Cloud9 doesn't have the ability to provide userdata
        # Because of this we need to use SSM run command
        cloud9_instance = cloud9.Ec2Environment(self, 'ResearchWorkspace', vpc=vpc, instance_type=ec2.InstanceType(instance_type_identifier='c5.large'))
        cdk.CfnOutput(self, 'Research Workspace URL',  value=cloud9_instance.ide_url)


        # Create a keypair in lambda and store the private key in SecretsManager
        c9_createkeypair_role = iam.Role(self, 'Cloud9CreateKeypairRole', assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'))
        c9_createkeypair_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'))
        # Add IAM permissions to the lambda role
        c9_createkeypair_role.add_to_policy(iam.PolicyStatement(
            actions=[
                'ec2:CreateKeyPair',
                'ec2:DeleteKeyPair'
            ],
            resources=['*'],
        ))

        # Lambda for Cloud9 keypair
        c9_createkeypair_lambda = _lambda.Function(self, 'C9CreateKeyPairLambda',
            runtime=_lambda.Runtime.PYTHON_3_6,
            handler='lambda_function.handler',
            timeout=cdk.Duration.seconds(300),
            role=c9_createkeypair_role,
            code=_lambda.Code.asset('functions/source/c9keypair'),
        )

        c9_createkeypair_provider = cr.Provider(self, "C9CreateKeyPairProvider", on_event_handler=c9_createkeypair_lambda)

        c9_createkeypair_cr = cfn.CustomResource(self, "C9CreateKeyPair", provider=c9_createkeypair_provider,
            properties={
                'ServiceToken': c9_createkeypair_lambda.function_arn
            }
        )
        #c9_createkeypair_cr.node.add_dependency(instance_id)
        c9_ssh_private_key_secret = secretsmanager.CfnSecret(self, 'SshPrivateKeySecret',
             secret_string=c9_createkeypair_cr.get_att_string('PrivateKey')
        )

        # The iam policy has parameters like <REGION> that need to be replaced.
        # We do it programmatically so future versions of the synth'd stack
        # template include all regions.
        key_vals={
            '<AWS ACCOUNT ID>': self.account,
            '<PARALLELCLUSTER EC2 ROLE NAME>': 'parallecluster-*',
            '<REGION>': [r.name for r in region_info.RegionInfo.regions],
            '<RESOURCES S3 BUCKET>': [data_bucket.bucket_name, 'parallelcluster-*']
        }
        parallelcluster_user_policy=[]
        with open('iam/ParallelClusterUserPolicy.json') as json_file:
            data = json.load(json_file)

            # Inner def replaces strings and expands lists
            # Inputs:
            #   - mykey (str): key to search for
            #   - myr (str): string to search within
            #   - myval (str or list): replacement value to substitute for mykey
            # Output:
            #   - (list): a list containing either [string] (i.e., a list containing the string)
            #           or [string1, string2, ...] (i.e., expanded list of strings)
            def repl(mykey, myr, myval):
                if mykey in myr:
                    if type(myval) is list:
                        # Replace with an expansion list
                        #print('~~~~~~~in> %s' % (myr))
                        temp=[]
                        for item in myval:
                            temp.append(myr.replace(mykey, item))
                        #print('~~~~~~out> %s' % (temp))
                        return temp
                    else:
                        # Replace with a str
                        #print('-------in> %s' % (myr))
                        myr = myr.replace(mykey, myval)
                        #print('------out> %s' % (myr))
                        return [myr]
                else:
                    # No replace
                    return [myr]
            # End def

            for index, policy in enumerate(data):
                for s in policy['PolicyDocument']['Statement']:
                    # Force all resources to be lists
                    if type(s['Resource']) is not list:
                        s['Resource'] = [s['Resource']]
                    # buffer resource to make multiple passes
                    buf = s['Resource']
                    for key, val in key_vals.items():
                        tbuf = []
                        for r in buf:
                            # extend flattens lists of expansion lists (e.g., if multiple keys appear in same resource)
                            tbuf.extend(repl(key, r, val))
                        buf = tbuf
                    s['Resource'] = buf

                parallelcluster_user_policy.append(iam.CfnManagedPolicy(self, policy['PolicyName'], policy_document=iam.PolicyDocument.from_json(policy['PolicyDocument'])))
                with open('iam/out_%s.json' % (index), 'w') as json_out:
                    json_out.write(json.dumps(policy['PolicyDocument'], indent=4))

        # ParallelCluster requires users create this role to enable SpotFleet
        spotfleet_role = iam.CfnServiceLinkedRole(self, 'SpotFleetServiceLinkedRole', aws_service_name='spotfleet.amazonaws.com')
        spotfleet_role.cfn_options.deletion_policy = cdk.CfnDeletionPolicy.RETAIN
        spotfleet_role.cfn_options.update_replace_policy = cdk.CfnDeletionPolicy.RETAIN
        spot_role = iam.CfnServiceLinkedRole(self, 'SpotServiceLinkedRole', aws_service_name='spot.amazonaws.com')
        spot_role.cfn_options.deletion_policy = cdk.CfnDeletionPolicy.RETAIN
        spot_role.cfn_options.update_replace_policy = cdk.CfnDeletionPolicy.RETAIN

        # Cloud9 IAM Role
        cloud9_role = iam.Role(self, 'Cloud9Role', assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'))
        cloud9_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'))
        cloud9_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AWSCloud9User'))
        for i, p in enumerate(parallelcluster_user_policy):
            cloud9_role.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, 'AttachParallelClusterUserPolicy%d' % (i), p.ref))
        cloud9_role.add_to_policy(iam.PolicyStatement(
            resources=['*'],
            actions=[
                'ec2:DescribeInstances',
                'ec2:DescribeVolumes',
                'ec2:ModifyVolume'
            ]
        ))
        cloud9_role.add_to_policy(iam.PolicyStatement(
            resources=[c9_ssh_private_key_secret.ref],
            actions=[
                'secretsmanager:GetSecretValue'
            ]
        ))
        cloud9_role.add_to_policy(iam.PolicyStatement(
            actions=[
             "s3:Get*",
             "s3:List*"
            ],
            resources=[
                "arn:aws:s3:::%s/*" % (data_bucket.bucket_name),
                "arn:aws:s3:::%s" % (data_bucket.bucket_name)
            ]
        ))

        bootstrap_script.grant_read(cloud9_role)
        pcluster_post_install_script.grant_read(cloud9_role)
        pcluster_config_script.grant_read(cloud9_role)

        create_user = cdk.CfnParameter(self, "CreateUserAndGroups", default="false", type="String", allowed_values=['true','false'], description='Provision an additional IAM user (Researcher) account and Admin/PowerUser groups to simplify onboarding multiple users in one account. Note: this requires IAM permissions to create a user and group.')
        user_condition = cdk.CfnCondition(self, "UserCondition", expression=cdk.Fn.condition_equals(create_user.value_as_string, "true"))

        # Admin Group
        admin_group = iam.CfnGroup(self, 'AdminGroup',
                                   managed_policy_arns=[iam.ManagedPolicy.from_aws_managed_policy_name('AdministratorAccess').managed_policy_arn,
                                                        iam.ManagedPolicy.from_aws_managed_policy_name('AWSCloud9Administrator').managed_policy_arn])
        admin_group.cfn_options.condition=user_condition

        # PowerUser Group
        poweruser_group = iam.CfnGroup(self, 'PowerUserGroup',
                                    managed_policy_arns=[iam.ManagedPolicy.from_aws_managed_policy_name('PowerUserAccess').managed_policy_arn,
                                                        iam.ManagedPolicy.from_aws_managed_policy_name('AWSCloud9Administrator').managed_policy_arn])
        poweruser_group.cfn_options.condition=user_condition

        # HPC User
        user = iam.CfnUser(self, 'Researcher',
                           groups=[admin_group.ref],
                           login_profile=iam.CfnUser.LoginProfileProperty(
                                   password_reset_required=True,
                                   password=cdk.SecretValue.cfn_parameter(password).to_string()
                               )
                           )

        user.cfn_options.condition = user_condition

        cdk.CfnOutput(self, 'UserLoginUrl', value="".join(["https://", self.account,".signin.aws.amazon.com/console"]), condition=user_condition)
        cdk.CfnOutput(self, 'UserName', value=user.ref, condition=user_condition )

        base_os = cdk.CfnParameter(self, "Operating System", default="alinux2", type="String", allowed_values=['alinux', 'alinux2', 'centos7', 'centos8', 'ubuntu1604', 'ubuntu1804'])
        cdk.CfnOutput(self, 'OS. Warning: noTears post_install is designed for ubuntu1804 and alinux2. Use other OS options at your own risk.', value=base_os.value_as_string)

        # Cloud9 Setup IAM Role
        cloud9_setup_role = iam.Role(self, 'Cloud9SetupRole', assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'))
        cloud9_setup_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'))
        # Allow pcluster to be run in bootstrap
        for i, p in enumerate(parallelcluster_user_policy):
            cloud9_setup_role.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, 'AttachParallelClusterUserPolicySetup%d' % (i), p.ref))

        # Add IAM permissions to the lambda role
        cloud9_setup_role.add_to_policy(iam.PolicyStatement(
            actions=[
                'cloudformation:DescribeStackResources',
                'ec2:AssociateIamInstanceProfile',
                'ec2:AuthorizeSecurityGroupIngress',
                'ec2:DescribeInstances',
                'ec2:DescribeInstanceStatus',
                'ec2:DescribeInstanceAttribute',
                'ec2:DescribeIamInstanceProfileAssociations',
                'ec2:DescribeVolumes',
                'ec2:DesctibeVolumeAttribute',
                'ec2:DescribeVolumesModifications',
                'ec2:DescribeVolumeStatus',
                'ssm:DescribeInstanceInformation',
                'ec2:ModifyVolume',
                'ec2:ReplaceIamInstanceProfileAssociation',
                'ec2:ReportInstanceStatus',
                'ssm:SendCommand',
                'ssm:GetCommandInvocation',
                's3:GetObject',
                'lambda:AddPermission',
                'lambda:RemovePermission',
                'events:PutRule',
                'events:DeleteRule',
                'events:PutTargets',
                'events:RemoveTargets',
                'cloud9:CreateEnvironmentMembership',
            ],
            resources=['*'],
        ))

        cloud9_setup_role.add_to_policy(iam.PolicyStatement(
            actions=[
                'iam:PassRole',
                'iam:CreateRole'
            ],
            resources=[cloud9_role.role_arn]
        ))

        cloud9_setup_role.add_to_policy(iam.PolicyStatement(
            actions=[
                'lambda:AddPermission',
                'lambda:RemovePermission'
            ],
            resources=['*']
        ))

        # Cloud9 Instance Profile
        c9_instance_profile = iam.CfnInstanceProfile(self, "Cloud9InstanceProfile", roles=[cloud9_role.role_name])

        # Lambda to add Instance Profile to Cloud9
        c9_instance_profile_lambda = _lambda.Function(self, 'C9InstanceProfileLambda',
            runtime=_lambda.Runtime.PYTHON_3_6,
            handler='lambda_function.handler',
            timeout=cdk.Duration.seconds(900),
            role=cloud9_setup_role,
            code=_lambda.Code.asset('functions/source/c9InstanceProfile'),
        )

        c9_instance_profile_provider = cr.Provider(self, "C9InstanceProfileProvider",
            on_event_handler=c9_instance_profile_lambda,
        )

        instance_id = cfn.CustomResource(self, "C9InstanceProfile", provider=c9_instance_profile_provider,
            properties={
                'InstanceProfile': c9_instance_profile.ref,
                'Cloud9Environment': cloud9_instance.environment_id,
            }
        )
        instance_id.node.add_dependency(cloud9_instance)

        # Lambda for Cloud9 Bootstrap
        c9_bootstrap_lambda = _lambda.Function(self, 'C9BootstrapLambda',
            runtime=_lambda.Runtime.PYTHON_3_6,
            handler='lambda_function.handler',
            timeout=cdk.Duration.seconds(900),
            role=cloud9_setup_role,
            code=_lambda.Code.asset('functions/source/c9bootstrap'),
        )

        c9_bootstrap_provider = cr.Provider(self, "C9BootstrapProvider", on_event_handler=c9_bootstrap_lambda)

        c9_bootstrap_cr = cfn.CustomResource(self, "C9Bootstrap", provider=c9_bootstrap_provider,
            properties={
                'Cloud9Environment': cloud9_instance.environment_id,
                'BootstrapPath': 's3://%s/%s' % (bootstrap_script.s3_bucket_name, bootstrap_script.s3_object_key),
                'Config': config,
                'BaseOS': base_os.value_as_string,
                'VPCID': vpc.vpc_id,
                'MasterSubnetID': vpc.public_subnets[0].subnet_id,
                'ComputeSubnetID': vpc.private_subnets[0].subnet_id,
                'AdditionalSG': pcluster_sg.security_group_id,
                'PostInstallScriptS3Url':  "".join( ['s3://', pcluster_post_install_script.s3_bucket_name,  "/", pcluster_post_install_script.s3_object_key ] ),
                'PostInstallScriptBucket': pcluster_post_install_script.s3_bucket_name,
                'S3ReadWriteResource': data_bucket.bucket_arn,
                'S3ReadWriteUrl': 's3://%s' % ( data_bucket.bucket_name ),
                'FSxID': cdk.Fn.condition_if(fsx_condition.logical_id, fsx_lustre_filesystem.ref, cdk.Aws.NO_VALUE),
                'KeyPairId':  c9_createkeypair_cr.ref,
                'KeyPairSecretArn': c9_ssh_private_key_secret.ref,
                'UserArn': cdk.Fn.condition_if(user_condition.logical_id, user.ref, cdk.Aws.NO_VALUE),
                'PclusterVersion': pcluster_version.value_as_string,
                'SpackVersion': spack_version.value_as_string,
                'SpackConfigURI': spack_config_uri,
            }
        )
        c9_bootstrap_cr.node.add_dependency(instance_id)
        c9_bootstrap_cr.node.add_dependency(c9_createkeypair_cr)
        c9_bootstrap_cr.node.add_dependency(c9_ssh_private_key_secret)
        c9_bootstrap_cr.node.add_dependency(data_bucket)
        c9_bootstrap_cr.node.add_dependency(spot_role)
        c9_bootstrap_cr.node.add_dependency(spotfleet_role)

        create_budget = cdk.CfnParameter(self, "EnableBudget", default="true", type="String", allowed_values=['true','false'])
        budget_limit = cdk.CfnParameter(self, 'BudgetLimit', description='The initial budget for this project in USD ($).', default=2000, type='Number')
        # Budgets
        budget_properties = {
            'budgetType': "COST",
            'timeUnit': "ANNUALLY",
            'budgetLimit': {
                'amount': budget_limit.value_as_number,
                'unit': "USD",
            },
            'costFilters': None,
            'costTypes': {
                'includeCredit': False,
                'includeDiscount': True,
                'includeOtherSubscription': True,
                'includeRecurring': True,
                'includeRefund': True,
                'includeSubscription': True,
                'includeSupport': True,
                'includeTax': True,
                'includeUpfront': True,
                'useAmortized': False,
                'useBlended': False,
            },
            'plannedBudgetLimits': None,
            'timePeriod': None,
        }
        email_address = cdk.CfnParameter(self, 'NotificationEmail', description='This email address will receive billing alarm notifications when 80% of the budget limit is reached.', default='email@amazon.com')
        email = {
            'notification': {
                'comparisonOperator': "GREATER_THAN",
                'notificationType': "ACTUAL",
                'threshold': 80,
                'thresholdType': "PERCENTAGE",
                },
            'subscribers': [{
                'address': email_address.value_as_string,
                'subscriptionType': "EMAIL",
            }]
        }

        overall_budget = budgets.CfnBudget(
            self,
            "HPCBudget",
            budget=budget_properties,
            notifications_with_subscribers=[email],
        )
        overall_budget.cfn_options.condition = cdk.CfnCondition(self, "BudgetCondition", expression=cdk.Fn.condition_equals(create_budget.value_as_string, "true"))



        self.template_options.metadata = {
            'AWS::CloudFormation::Interface': {
                'ParameterGroups': [
                    {
                        'Label': { 'default': 'ParallelCluster Configuration' },
                        'Parameters': [
                            pcluster_version.logical_id,
                            config.logical_id,
                            base_os.logical_id
                        ]
                    },
                    {
                        'Label': { 'default': 'Lustre Configuration' },
                        'Parameters': [
                            create_lustre.logical_id,
                            lustre_storage_capacity.logical_id,
                            lustre_type.logical_id,
                            lustre_import_policy.logical_id,
                            lustre_storage_type.logical_id,
                            lustre_performance.logical_id,
                            lustre_drive_cache.logical_id
                        ]
                    },
                    {
                        'Label': { 'default': 'Spack Configuration' },
                        'Parameters': [
                            spack_version.logical_id,
                            spack_config_uri.logical_id
                        ]
                    },
                    {
                        'Label': { 'default': 'Budget Configuration' },
                        'Parameters': [
                            create_budget.logical_id,
                            budget_limit.logical_id,
                            email_address.logical_id
                        ]
                    },
                    {
                        'Label': { 'default': 'User Configuration' },
                        'Parameters': [
                            create_user.logical_id,
                            password.logical_id
                        ]
                    }
                ]
            }
        }


        #  Connection related outputs. These outputs need to have prefix "MetaConnection"
        #  The "connections" are derived based on the CFN outputs as follows.
        #
        #  CFN outputs with the OutputKey having format "MetaConnection<ConnectionAttrib>" or "MetaConnection<N><ConnectionAttrib>"
        #  are used for extracting connection information.
        #  - If the environment has only one connection then it can have outputs with "MetaConnection<ConnectionAttrib>" format.
        #  - If it has multiple connections then it can have outputs with "MetaConnection<N><ConnectionAttrib>" format.
        #  For example, MetaConnection1Name, MetaConnection2Name, etc.
        #
        #  The expected CFN output variables used for capturing connections related information are as follows:
        #
        #  - MetaConnectionName (or MetaConnection<N>Name) - Provides name for connection
        #
        #  - MetaConnectionUrl (or MetaConnection<N>Url) - Provides connection url, if available
        #
        #  - MetaConnectionScheme (or MetaConnection<N>Scheme) - Provides connection protocol information such as http, https, ssh, jdbc, odbc etc
        #
        #  - MetaConnectionType (or MetaConnection<N>Type) - Provides type of the connection such as "SageMaker", "EMR", "FOO", "BAR" etc
        #
        #  - MetaConnectionInfo (or MetaConnection<N>Info) - Provides extra information required to form connection url.
        #  For example, in case of MetaConnectionType = SageMaker, the MetaConnectionInfo should provide SageMaker notebook
        #  instance name that can be used to form pre-signed SageMaker URL.
        #
        #  - MetaConnectionInstanceId (or MetaConnection<N>InstanceId) - Provides AWS EC2 instanceId of the instance to connect to when applicable.
        #  Currently this is applicable only when ConnectionScheme = 'ssh'.
        #  This instanceId will be used for sending user's SSH public key using AWS EC2 Instance Connect when user wants to SSH to the instance.
        #
        cdk.CfnOutput(self, 'MetaConnection1Name',  description='Name for connection', value='Open Research Workspace (AWS Cloud9 IDE)')
        cdk.CfnOutput(self, 'MetaConnection1Type',  description='Type of workspace', value='AWS Cloud9 IDE + AWS ParallelCluster')
        cdk.CfnOutput(self, 'MetaConnection1InstanceId',  description='EC2 Linux Instance Id', value=cloud9_instance.environment_id)
        cdk.CfnOutput(self, 'MetaConnection1Url',  description='URL for Cloud9 Workspace', value=cloud9_instance.ide_url )
        cdk.CfnOutput(self, 'MetaConnection1Scheme',  description='Protocol for connection', value='https')

        #cdk.CfnOutput(self, 'MetaConnection2Name',  description='Name for connection', value='SSH to Main EC2 instance')
        #cdk.CfnOutput(self, 'MetaConnection2InstanceId',  description='EC2 Linux Instance Id', value=pcluster_node.ref )
        #cdk.CfnOutput(self, 'MetaConnection2Scheme',  description='Protocol for connection', value='ssh')

        #### END SWB #####
