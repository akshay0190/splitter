#!/usr/bin/env python3
import os
import logging
from logging.config import fileConfig


dirname = os.path.dirname(__file__)
fileConfig(os.path.join(dirname,"resources/logging_config.ini" ))
if "LOG_LEVEL" in os.environ:
    logging.getLogger().setLevel(os.environ["LOG_LEVEL"])
import jsii
from aws_cdk import(
    core,
    aws_iam as aws_iam,
    aws_logs
)
from stack_handler import CDKStack

release_environment = "dev"
stack_name = "anl-vip-{}-csv-filesplitter".format(release_environment)
default_event_bus_arn = f"arn:aws:events:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:event-bus/default"
vpc_id= "vpc-0eea84e35dd620f5a" if release_environment in ["dev","test"] else "vpc-091283484c90d492a"
security_group_id = "sg-03fccf101bfb35c3d" if release_environment in ["dev"] else ""
subnet_id = "'subnet-0c0129d517a5fc6cf', 'subnet-0f4e03516484d85d9'" if release_environment in  ["dev"] else ""
cdk_environment = core.Environment(
    account = os.environ["CDK_DEFAULT_ACCOUNT"],
    region= os.environ["CDK_DEFAULT_REGION"]
)

parameters = {
    "Environment" : release_environment,
    "DefaultEventBusArn": default_event_bus_arn,
    "NetworkConfiguration":{
        "vpc_id": vpc_id,
        "security_group_id": security_group_id,
        "subnet_id":subnet_id
        },
}
app = core.App()
stack = CDKStack(scope=app, id= stack_name, parameters=parameters, env=cdk_environment)
app.synth()