import os

ENVIRONMENT = os.environ.get("P_ENVIRONMENT")
LOG_LEVEL = os.environ.get("LOG_LEVEL", 'INFO')


log_group_name_consumer = os.environ.get("P_LOG_GROUP_NAME")

request_payload_region = os.environ.get("P_REQUEST_PAYLOAD_REGION", 'eu-west-1')

ecr_repository_name = os.environ.get("P_ECR_REPOSITORY_NAME")
#source_bucket = os.environ.get("P_SOURCE_BUCKET")
target_bucket = os.environ.get("P_TGT_BUCKET")
kms_key = os.environ.get("P_KMS_KEY")
