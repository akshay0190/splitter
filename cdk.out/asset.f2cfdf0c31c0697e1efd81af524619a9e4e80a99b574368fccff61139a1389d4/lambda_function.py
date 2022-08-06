from urllib import response
import boto3
from datetime import datetime
import json
import os

p_regionName = 'us-east-1'
p_cluster_name=os.environ["p_cluster_name"]
p_launch_type='FARGATE'
p_task_definition=os.environ["task_definition"]
subnet_id = os.environ["subnet_id"]
security_group = os.environ["security_group"]
client = boto3.client('ecs',region_name=p_regionName)

def lambda_handler(event,context):
    print('Lambda Function Started')

    bucket_name = event['Records'][0]['s3']['bucket']['name']
    bucket_object_key =event['Records'][0]['s3']['object']['key']

    print(f'Bucket Name: {bucket_name}')
    print(f'Bucket Object Key: {bucket_object_key}')
    print(p_cluster_name)
    print(p_task_definition)
    print(security_group)
    for i in subnet_id:
        print(i) 
    print("running task")

    response = client.run_task(
        cluster=p_cluster_name,
        launchType=p_launch_type,
        taskDefinition=p_task_definition,
        count=1,
        networkConfiguration={
            'awsvpcConfiguration':{
                'subnets': [subnet_id],
                'securityGroups': [security_group,],
                'assignPublicIp':'DISABLED'
            }

        }

    )
    print("Finished invoking task")
    print(response)