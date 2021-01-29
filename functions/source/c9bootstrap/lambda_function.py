# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from __future__ import print_function
import logging
from time import sleep
import boto3
from crhelper import CfnResource

logger = logging.getLogger(__name__)
helper = CfnResource(json_logging=True, log_level='DEBUG', boto_level='CRITICAL')

try:
    ssm_client = boto3.client('ssm')
    cloud9_client = boto3.client('cloud9')
except Exception as e:
    helper.init_failure(e)

def grant_permissions_cloud9(cloud9_environment, user_arn):
    return cloud9_client.create_environment_membership(environmentId=cloud9_environment, userArn=user_arn, permissions='read-write')

def get_command_output(instance_id, command_id):
    response = ssm_client.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
    if response['Status'] in ['Pending', 'InProgress', 'Delayed']:
        return
    return response


def send_command(instance_id, commands):
    logger.debug("Sending command to %s : %s" % (instance_id, commands))
    try:
        return ssm_client.send_command(InstanceIds=[instance_id], DocumentName='AWS-RunShellScript',
                                       Parameters={'commands': commands})
    except ssm_client.exceptions.InvalidInstanceId:
        logger.debug("Failed to execute SSM command", exc_info=True)
        return

def wait_instance_ready(cloud9_environment, context):
    # Given a unique ID for a Cloud9 environment, this waits until
    # the EC2 instance is instantiated (PingStatus 'Online'), and
    # returns the InstanceId. Timeout of 20000 milliseconds.

    while True:
        # Filters SSM Managed Instances to find only the matching cloud9 env
        instance_info = ssm_client.describe_instance_information(Filters=[{
            'Key': 'tag:aws:cloud9:environment', 'Values': [ "{}".format(cloud9_environment)]
        }])
        # if instance not found/not registered to SSM, instance_info is empty.
        if instance_info.get('InstanceInformationList'):
            if instance_info.get('InstanceInformationList')[0].get('PingStatus') == 'Online':
                return instance_info.get('InstanceInformationList')[0].get('InstanceId')
        if context.get_remaining_time_in_millis() < 20000:
            raise Exception("Timed out waiting for instance to be ready")
        sleep(15)

@helper.create
def create(event, context):
    logger.debug("Got Create")
    cloud9_environment = event['ResourceProperties']['Cloud9Environment']
    instance_id = wait_instance_ready(cloud9_environment, context)
    bootstrap_path = event['ResourceProperties']['BootstrapPath']
    vpc_id = event['ResourceProperties']['VPCID']
    master_subnet_id = event['ResourceProperties']['MasterSubnetID']
    compute_subnet_id = event['ResourceProperties']['ComputeSubnetID']
    post_install_script_url = event['ResourceProperties']['PostInstallScriptS3Url']
    keypair_id = event['ResourceProperties']['KeyPairId']
    keypair_secret_arn = event['ResourceProperties']['KeyPairSecretArn']
    post_install_script_bucket = event['ResourceProperties']['PostInstallScriptBucket']
    s3_read_write_resource = event['ResourceProperties']['S3ReadWriteResource']
    s3_read_write_url = event['ResourceProperties']['S3ReadWriteUrl']
    fsx_id = event['ResourceProperties']['FsxID']
    user_arn = event['ResourceProperties']['UserArn']
    config = event['ResourceProperties']['Config']
    base_os_choice = event['ResourceProperties']['BaseOSChoice']
    pcluster_version = event['ResourceProperties']['PclusterVersion']

    # grant s3 permissions
    grant_permissions_cloud9(cloud9_environment, user_arn)

    fsx_str = ''
    if(fsx_id is not 'false'):
        fsx_str = ' fsx_id=' + fsx_id

    command = ['mkdir -p /tmp/setup', 'cd /tmp/setup',
                'aws s3 cp ' + bootstrap_path + ' bootstrap.sh --quiet',
                'chmod 755 bootstrap.sh',
                'sudo -u ec2-user '
                + ' vpc_id=' + vpc_id
                + ' master_subnet_id=' + master_subnet_id
                + ' compute_subnet_id=' + compute_subnet_id
                + ' post_install_script_url=' + post_install_script_url
                + ' post_install_script_bucket=' + post_install_script_bucket
                + ' s3_read_write_resource=' + s3_read_write_resource
                + ' s3_read_write_url=' + s3_read_write_url
                + fsx_str
                + ' private_key_arn=' + keypair_secret_arn
                + ' ssh_key_id=' + keypair_id
                + ' config=' + config
                + ' base_os_choice=' + base_os_choice
                + ' pcluster_version=' + pcluster_version
                + ' cloud9_environment=' + cloud9_environment
                + ' bash bootstrap.sh']
    send_response = send_command(instance_id, command)
    if send_response:
        helper.Data["CommandId"] = send_response['Command']['CommandId']


@helper.poll_create
def poll_create(event, context):
    logger.info("Got create poll")
    instance_id = wait_instance_ready(event['ResourceProperties']['Cloud9Environment'], context)
    while True:
        try:
            cmd_output_response = get_command_output(instance_id, helper.Data["CommandId"])
            if cmd_output_response:
                break
        except ssm_client.exceptions.InvocationDoesNotExist:
            logger.debug('Invocation not available in SSM yet', exc_info=True)
        if context.get_remaining_time_in_millis() < 20000:
            return
        sleep(15)
    if cmd_output_response['StandardErrorContent']:
        raise Exception("ssm command failed: " + cmd_output_response['StandardErrorContent'][:235])
    return instance_id


@helper.update
@helper.delete
def no_op(_, __):
    return


def handler(event, context):
    helper(event, context)
