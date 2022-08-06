from inspect import Parameter
from re import A
import re
from tkinter import image_names
from aws_cdk import (
    core as cdk,
    aws_iam as _iam,
    aws_s3 as _s3,
    aws_kms as _kms,
    aws_lambda as _lambda,
    aws_ec2 as _ec2,
    aws_s3_notifications as _s3_notification,
    aws_events as _events,
    aws_events_targets as _events_targets,
    aws_lambda_destinations as _lambda_destinations,
    aws_ecr as _ecr,
    aws_ecs as _ecs,
    aws_logs as _logs

    # aws_sqs as sqs,
)
#from constructs import Construct

class CDKStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, parameters:dict, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        iam_role_name = "anl-vip-{}-iam-input-filesplitter".format(parameters["Environment"])
        lambda_execution_role_policy_name='service-role/AWSLambdaVPCAccessExecutionRole'
        ecs_task_execution_policy_name='service-role/AmazonECSTaskExecutionRolePolicy'

        iam_generic_role_mutable = _iam.Role(
            self,
            "fileSplitterLambdaIAMRole",
            assumed_by=_iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name=iam_role_name
        )
        iam_generic_role_mutable.add_managed_policy(
            _iam.ManagedPolicy.from_aws_managed_policy_name(lambda_execution_role_policy_name)
        )

        iam_generic_role_mutable.add_managed_policy(
            _iam.ManagedPolicy.from_aws_managed_policy_name(ecs_task_execution_policy_name)
        )

        outputOfLambdaIAMRoleName = cdk.CfnOutput(
            self,
            "outputLambdaIAMRole",
            value=iam_generic_role_mutable.role_arn,
            description="IAM Role used by Lambda Function",
            export_name= "FileSplitterLambdaIAMRole"
        )

        kms_key_name = "anl-vip-{}-kms-input-filesplitter".format(parameters["Environment"])
        generic_key=_kms.Key(scope=self,id="GenericKMSKey",
        alias=f"alias/{kms_key_name}",
        description="check key",
        enable_key_rotation=True,
        removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        generic_key.node.default_child.add_override("Properties.PendingWindowInDays", 7)

        kmskeyoutput = cdk.CfnOutput(
            self,
            "GenKmsKeyOutput",
            value=generic_key.key_arn,
            description="generic key",
            export_name="FileSplitterKMSKey"
        )
        
        

        source_s3_bucket_name = "anl-vip-{}-s3-input-filesplitter-src".format(parameters["Environment"])

        src_s3_bucket = _s3.Bucket(
            self,
            "src_s3_bucket",
            versioned=True,
            access_control=_s3.BucketAccessControl.PRIVATE,
            encryption=_s3.BucketEncryption.KMS,
            encryption_key=generic_key,
            removal_policy=cdk.RemovalPolicy.DESTROY,

        )




        

        iam_policy_statement_s3_src_bucket_deny_nonsse1_request = _iam.PolicyStatement(
            effect=_iam.Effect.DENY,
            sid='AllowSSLRequestsOnly',
            principals=[_iam.Anyone()],
            actions=['s3:*'],
            conditions={
                "Bool":{"aws:SecureTransport":"false"}
            },
            resources=[f'{src_s3_bucket.bucket_arn}',
            f'{src_s3_bucket.bucket_arn}/*',
            ]

        )
        iam_policy_statement_s3_src_bucket_deny_nonsse_request = _iam.PolicyStatement(
            effect=_iam.Effect.DENY,
            sid='AllowSSEForKmsRequestsOnly',
            principals=[_iam.Anyone()],
            actions=['s3:putobject'],
            conditions={
                'StringNotEquals':{'s3:x-amz-server-side-encryption':'aws:kms'},
            
                'Null':{'s3:x-amz-server-side-encryption':'true'}
                },
            resources=[
            f'{src_s3_bucket.bucket_arn}/*',
            ]

        )
        src_s3_bucket.add_to_resource_policy(iam_policy_statement_s3_src_bucket_deny_nonsse1_request)
        src_s3_bucket.add_to_resource_policy(iam_policy_statement_s3_src_bucket_deny_nonsse_request)

        outputSrcBucket = cdk.CfnOutput(
            self,
            "SourceS3Bucket",
            value=src_s3_bucket.bucket_name,
            description="Source Bucket",
            export_name="FileSpliterSrcBucket"

        )


       
        target_s3_bucket_name = "anl-vip-{}-s3-input-filesplitter-tgt".format(parameters["Environment"])

        tgt_s3_bucket = _s3.Bucket(
            self,
            "tgt_s3_bucket",
            versioned=True,
            access_control=_s3.BucketAccessControl.PRIVATE,
            encryption=_s3.BucketEncryption.KMS,
            encryption_key=generic_key,
            removal_policy=cdk.RemovalPolicy.DESTROY,

        )


        iam_policy_statement_s3_tgt_bucket_deny_nonsse1_request = _iam.PolicyStatement(
            effect=_iam.Effect.DENY,
            sid='AllowSSLRequestsOnly',
            principals=[_iam.Anyone()],
            actions=['s3:*'],
            conditions={
                "Bool":{"aws:SecureTransport":"false"}
            },
            resources=[f'{tgt_s3_bucket.bucket_arn}',
            f'{tgt_s3_bucket.bucket_arn}/*',
            ]

        )
        iam_policy_statement_s3_tgt_bucket_deny_nonsse_request = _iam.PolicyStatement(
            effect=_iam.Effect.DENY,
            sid='AllowSSEForKmsRequestsOnly',
            principals=[_iam.Anyone()],
            actions=['s3:putobject'],
            conditions={
                'StringNotEquals':{'s3:x-amz-server-side-encryption':'aws:kms'},
            
                'Null':{'s3:x-amz-server-side-encryption':'true'}
                },
            resources=[
            f'{tgt_s3_bucket.bucket_arn}/*',
            ]

        )
        tgt_s3_bucket.add_to_resource_policy(iam_policy_statement_s3_tgt_bucket_deny_nonsse1_request)
        tgt_s3_bucket.add_to_resource_policy(iam_policy_statement_s3_tgt_bucket_deny_nonsse_request)

        outputTgtBucket = cdk.CfnOutput(
            self,
            "TargetS3Bucket",
            value=tgt_s3_bucket.bucket_name,
            description="Target Bucket",
            export_name="FileSpliterSgtBucket"

        )

        ecs_ecr_stack_name = "anl-vip-{}-input-filesplitter".format(parameters["Environment"])
        
        repository = _ecr.Repository(
            scope=self,
            id="ECRRepository",
            repository_name=ecs_ecr_stack_name,
            image_scan_on_push=True,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )
        cdk.CfnOutput(
            scope=self,
            id="ECRRepositoryName",
            value=repository.repository_name,
            description="to be used to push docker image of application name:{}".format(ecs_ecr_stack_name)
            )
        
        task_definition = _ecs.FargateTaskDefinition(
            scope=self,
            id="TaskDefinition",
            family=ecs_ecr_stack_name
        )
        
        task_definition.add_container(
            id="TaskDefinitionFileSplitter",
            image=_ecs.ContainerImage.from_ecr_repository(repository=repository),
            environment={
                "P_ECR_REPOSITORY_NAME":repository.repository_name,
                "P_LOG_GROUP_NAME":ecs_ecr_stack_name,
                "P_ENVIRONMENT":parameters["Environment"],
                "P_REQUEST_PAYLOAD_REGION":self.region,
                
                "P_TGT_BUCKET":tgt_s3_bucket.bucket_name,
                "P_KMS_KEY":generic_key.key_id
            },
            logging=_ecs.LogDriver.aws_logs(
                log_group=_logs.LogGroup(
                    scope=self,
                    id="CloudWatchLogGroup",
                    log_group_name="ecs/{}".format(ecs_ecr_stack_name),
                    retention=_logs.RetentionDays.TWO_MONTHS

                ),
                stream_prefix="ecs"
            )
        )

        cdk.CfnOutput(
            scope=self,
            id="ECSTaskDefinitionArn",
            value=task_definition.task_definition_arn,
            description="To be described"
        )
        generic_key.grant_encrypt_decrypt(grantee=task_definition.task_role)

        task_definition_policy_statement_s3_read =_iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            actions=["s3:*"],
            resources=[f'{src_s3_bucket.bucket_arn}',
            f'{src_s3_bucket.bucket_arn}/*',
            ]

        )
        task_definition_policy_statement_s3_write=_iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            actions=["s3:*"],
            resources=[f'{tgt_s3_bucket.bucket_arn}',
            f'{tgt_s3_bucket.bucket_arn}/*',
            ]

        )
        task_definition_policy_statement_cw_log=_iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            actions=["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents" ],
            resources=["*"]

        )
        task_definition.add_to_task_role_policy(task_definition_policy_statement_s3_read)
        task_definition.add_to_task_role_policy(task_definition_policy_statement_s3_write)
        task_definition.add_to_task_role_policy(task_definition_policy_statement_cw_log)

        ECSFargateCluster = _ecs.Cluster(
            scope=self,
            id= "ECSFarGateCluster",
            cluster_name=ecs_ecr_stack_name

        )

        
        

        

        lambda_function_name = "anl-vip-{}-lambda-input-filesplitter".format(parameters["Environment"])
        lambda_src_code_path = _lambda.AssetCode('./lambda_src/csv_file_splitter')
        filesplitter_function = _lambda.Function(scope=self,id="FileSPlitterFunctionId",
        function_name=lambda_function_name,
        description="splitter function",
        code=lambda_src_code_path,
        handler="lambda_function.lambda_handler",
        runtime= _lambda.Runtime.PYTHON_3_8,
        timeout=cdk.Duration.seconds(amount=900),
        memory_size=256,
        role=iam_generic_role_mutable,
        
        vpc=_ec2.Vpc.from_lookup(self, "VPC", vpc_id=parameters["NetworkConfiguration"]["vpc_id"]),
        vpc_subnets=_ec2.SubnetSelection(subnet_type=_ec2.SubnetType.PUBLIC),
        allow_public_subnet=True,
        security_groups=[_ec2.SecurityGroup.from_security_group_id(scope=self,id="SecurityGroup",
        security_group_id=parameters["NetworkConfiguration"]["security_group_id"], mutable=False)],
        environment={
               "p_cluster_arn": ECSFargateCluster.cluster_arn,
               "task_definition" : task_definition.task_definition_arn,
               "subnet_id": parameters["NetworkConfiguration"]["subnet_id"],
               "security_group":parameters["NetworkConfiguration"]["security_group_id"]
        }
        )

        test_custom_policy_ecs = {
                "Version": "2012-10-17",
                "Statement": [
                {
                "Effect": "Allow",
                "Action": [
                "ecs:*"
                ],
                "Condition": {
                    "ArnEquals": {
                    "ecs:cluster": ECSFargateCluster.cluster_arn
                }
                },
                "Resource": [
                            task_definition.task_definition_arn
                ]
                }
                ]
            }
        
        custom_policy_document = _iam.PolicyDocument.from_json(test_custom_policy_ecs)
        new_inline_policy = _iam.Policy(
            self, 
            "MyNewPolicy"
            ,document=custom_policy_document)
        filesplitter_function.role.attach_inline_policy(new_inline_policy)
        policy_document_pass_role = {
            "Version": "2012-10-17",
            "Statement": [{
            "Effect": "Allow",
                "Action": [
                    "iam:GetRole",
                    "iam:PassRole"
                ],
                "Resource": "arn:aws:iam::{}:role/anl-vip-{}-csv-files*".format(self.account,parameters["Environment"])
            }]
        }

        custom_policy_document_for_pass_role = _iam.PolicyDocument.from_json(policy_document_pass_role)
        new_pass_role_policy = _iam.Policy(
            self, 
            "PassRolePolicyForLambdaECS",
            document=custom_policy_document_for_pass_role
            )
        filesplitter_function.role.attach_inline_policy(new_pass_role_policy)
        src_s3_bucket.node.add_dependency(filesplitter_function)
        src_s3_bucket.add_event_notification(
            _s3.EventType.OBJECT_CREATED,
            _s3_notification.LambdaDestination(filesplitter_function)
        )


