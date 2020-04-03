from __future__ import print_function
import logging
from time import sleep
import boto3
from crhelper import CfnResource

logger = logging.getLogger(__name__)
helper = CfnResource(json_logging=True, log_level='DEBUG', boto_level='CRITICAL')

try:
    ssm_client = boto3.client('ssm')
    ec2_client = boto3.client('ec2')
except Exception as e:
    helper.init_failure(e)


def get_command_output(instance_id, command_id):
    response = ssm_client.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
    if response['Status'] in ['Pending', 'InProgress', 'Delayed', 'Delivery Timed Out', 'Execution Timed Out', 'Failed', 'Canceled', 'Undeliverable', 'Terminated']:
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
    instance_id = event['ResourceProperties']['InstanceId']
    instance = ec2_client.describe_instances(Filters=[{'Name': 'instance-id', 'Values': [instance_id]}])['Reservations'][0]['Instances'][0]
    block_volume_id = instance['BlockDeviceMappings'][0]['Ebs']['VolumeId']
    size = event['ResourceProperties']['EBSVolumeSize']
    ec2_client.modify_volume(VolumeId=block_volume_id,Size=int(size))
    while True:
        commands = ['sudo growpart /dev/xvda 1']
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
    instance_id = event["ResourceProperties"]["InstanceId"]
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

