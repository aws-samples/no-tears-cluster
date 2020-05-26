# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import boto3
import cfnresponse
import traceback
import random
import string
import time

ec2_client = boto3.client('ec2')
ssm_client = boto3.client('ssm')

def handler(event, context):
   status = cfnresponse.SUCCESS
   data = {}
   if 'PhysicalResourceId' in event.keys():
       key_name = event['PhysicalResourceId']
   try:
       if event['RequestType'] == 'Create':
           key_name = event['StackId'].split('/')[1][0:255-9] + '-' + ''.join(random.choice(
              string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8)
           )
           data['PrivateKey'] = ec2_client.create_key_pair(KeyName=key_name)['KeyMaterial']
       elif event['RequestType'] == 'Delete':
           ec2_client.delete_key_pair(KeyName=key_name)
   except Exception:
       traceback.print_exc()
       status = cfnresponse.FAILED
   if event['RequestType'] == 'Delete':
       time.sleep(60) # give the logs some time to sync to cwl
   cfnresponse.send(event, context, status, data, key_name, noEcho=True)

