import boto3
import docker
import base64
import json
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger()

p_environment = "dev"
p_service_name = os.environ.get("RELEASE_DEFINITIONNAME", 'file-splitter-v0')
p_image_version_number = os.environ.get("P_IMAGE_VERSION_NUMBER", 'latest')
count_match = 0

local_tag = "latest"
version_number = p_image_version_number

session = boto3.session.Session()
current_region = session.region_name
client = session.client('ecr')
docker_api = docker.from_env()


def get_application_stack_name_ecr(environment, service_name):
    """Defines application name which should be used to get iam role and lambda role arn"""
    return "anl-vip-" + environment + "-" + service_name


repo_name = get_application_stack_name_ecr(p_environment, p_service_name)

logger.info("Step: 1 - Checking if this ECR repository" + repo_name + " exists.")
try:
    describe_response = client.describe_repositories(repositoryNames=[repo_name])
    for repositories in describe_response["repositories"]:
        try:
            repositories["repositoryArn"]
        except Exception as ex:
            ex_type, ex_value, ex_traceback = sys.exc_info()
            logger.error(ex_value)
        else:
            logger.warning("Step: 2 - ECR Repository already exist, Please check this URI mentioned." + repositories[
                "repositoryUri"])
            ecr_repo_name = repositories["repositoryUri"]

except Exception as ex:
    ex_type, ex_value, ex_traceback = sys.exc_info()
    logger.warning("Step: 2 - No {} ECR exist. {}".format(repo_name, ex_value))
    logger.warning("Hence, Creating ERC Repository with Repo name: " + repo_name)

    try:
        response = client.create_repository(repositoryName=repo_name, imageTagMutability='IMMUTABLE')
        logger.warning("Repository Created. ")
        logger.warning("Repository URI: " + response["repository"]["repositoryUri"])
        ecr_repo_name = response["repository"]["repositoryUri"]
    except Exception as e:
        logger.error(e)

logger.info("Step: 3 - Now checking if tag: " + version_number + " exists in ECR: " + ecr_repo_name)
response_iterator = client.list_images(repositoryName=repo_name)

for page in response_iterator['imageIds']:
    if page['imageTag'] == version_number:
        logger.info("Image with tag " + version_number + " found. Hence existing.")
        logger.info("Please Create a new tag by providing version in Azure variable p_image_version_number, "
                    "improve versioning. Thank You!!")
        count_match = count_match + 1
        exit(1)

if count_match == 0:
    logger.warning('ECR Image tag not found')

logger.info("Step: 4 - Building docker image with tag: " + version_number)
dockerLocation = os.path.abspath(os.path.dirname(__file__))
logger.info("this application base Docker file path is: " + os.path.join(dockerLocation, 'Dockerfile'))

# image, build_log = docker_api.images.build(path=dockerLocation,
docker_api.images.build(path=dockerLocation,
                        nocache=False,
                        rm=True,
                        tag='local_build',
                        dockerfile=os.path.join(dockerLocation, 'Dockerfile'))

logger.info("Step: 5 - Image Created with tag local_tag")

auth = client.get_authorization_token()
token = auth["authorizationData"][0]["authorizationToken"]
ecr_username, ecr_password = base64.b64decode(token).decode().split(':')
ecr_registry = auth["authorizationData"][0]["proxyEndpoint"]

logger.info("Step: 6 - Retrieve an authentication token and authenticate this Docker client to elastic container "
            "registry")
logger.info("Step: 7 - Tag " + version_number + " will be pushed to ECR : " + ecr_repo_name)
image = docker_api.images.get('local_build:latest')

# get Docker to login/authenticate with ECR
docker_api.login(username=ecr_username, password=ecr_password, registry=ecr_registry)
image.tag(ecr_repo_name, tag=version_number)
# push the image to ECR
push_log = docker_api.images.push(ecr_repo_name, tag=version_number)
logger.info(push_log)

logger.info("Step: 8 - Deleting local image: " + ecr_repo_name + ":" + version_number)
docker_api.images.remove(ecr_repo_name + ":" + version_number)
logger.info("Step: 9 - All above action are done now successfully")