from __future__ import print_function
import logging
from time import sleep
import boto3
from crhelper import CfnResource

logger = logging.getLogger(__name__)
helper = CfnResource(json_logging=True, log_level='DEBUG', boto_level='CRITICAL')

try:
    ec2_client = boto3.client('ec2')
    ssm_client = boto3.client('ssm')
except Exception as e:
    helper.init_failure(e)


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


@helper.create
def create(event, context):
    logger.debug("Got Create")
    response = ec2_client.describe_instances(Filters=[{
        'Name': 'tag:aws:cloud9:environment', 'Values': [event['ResourceProperties']['Cloud9Environment']]
    }])
    instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
    bootstrap_path = event['ResourceProperties']['BootstrapPath']
    arguments = event['ResourceProperties']['BootstrapArguments']
    vpc_id = event['ResourceProperties']['VPCID']
    master_subnet_id = event['ResourceProperties']['MasterSubnetID']
    compute_subnet_id = event['ResourceProperties']['ComputeSubnetID']

    while True:
        commands = ['mkdir -p /tmp/setup', 'cd /tmp/setup',
                    'aws --no-sign-request s3 cp ' + bootstrap_path + ' bootstrap.sh --quiet',
                    'sudo chmod +x bootstrap.sh',
                    'sudo -u ec2-user '
                    + ' vpc_id=' + vpc_id
                    + ' master_subnet_id=' + master_subnet_id
                    + ' compute_subnet_id=' + compute_subnet_id
                    + ' bash bootstrap.sh ' + arguments]
        send_response = send_command(instance_id, commands)
        if send_response:
            helper.Data["CommandId"] = send_response['Command']['CommandId']
            break
        if context.get_remaining_time_in_millis() < 20000:
            raise Exception("Timed out attempting to send command to SSM")
        sleep(15)


@helper.poll_create
def poll_create(event, context):
    logger.info("Got create poll")
    response = ec2_client.describe_instances(Filters=[{
        'Name': 'tag:aws:cloud9:environment', 'Values': [event['ResourceProperties']['Cloud9Environment']]
    }])
    instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
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
