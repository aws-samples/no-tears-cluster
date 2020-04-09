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


def ssm_ready(instance_id):
    try:
        response = ssm_client.describe_instance_information(Filters=[
            {'Key': 'InstanceIds', 'Values': [instance_id]}
            ])
        logger.debug(response)
        return True
    except ssm_client.exceptions.InvalidInstanceId:
        return False


@helper.create
def create(event, context):
    logger.debug("Got Create")
    response = ec2_client.describe_instances(Filters=[{
        'Name': 'tag:aws:cloud9:environment', 'Values': [event['ResourceProperties']['Cloud9Environment']]
    }])
    instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
    ec2_client.associate_iam_instance_profile(
        IamInstanceProfile={'Name': event['ResourceProperties']['InstanceProfile']},
        InstanceId=instance_id)
    while not ssm_ready(instance_id):
        if context.get_remaining_time_in_millis() < 20000:
            raise Exception("Timed out waiting for instance to register with SSM")
        sleep(15)
    return instance_id


@helper.update
@helper.delete
def no_op(_, __):
    return


def handler(event, context):
    helper(event, context)
