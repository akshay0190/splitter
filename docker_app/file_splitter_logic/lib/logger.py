import logging
import watchtower
import sys
from uuid import uuid4
from time import gmtime, strftime
import os

# from .boto_session import boto_session

LOGGER = None

'''
Setup logging
'''


def generate_current_time():
    """Generates current time

    Returns:
        Current time in GMT
    """
    current_time = strftime("%Y%m%d_%H-%M-%S", gmtime())
    return current_time


def generate_uuid():
    """Generates uuid

    Returns:
        generated uuid
    """
    generated_uuid = str(uuid4())
    return generated_uuid


def get_logger(log_group_name):
    """Retrieves the logger object
    
    Returns:
        Logger -- Logger instance
    """
    global LOGGER
    if LOGGER == None:
        LOGGER = create_logger(log_group_name)

    return LOGGER


def create_logger(log_group_name, custom_stream_name=None, cw_use_queues=True):
    """Creates a logger instance
    
    Returns:
        Logger -- Logger instance
    """
    logger = logging.getLogger()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    logger.setLevel(logging.INFO)
    current_time = generate_current_time()
    generated_uuid = generate_uuid()
    stream_name = f'{current_time}-{generated_uuid}' if custom_stream_name == None else custom_stream_name
    cw_logger = watchtower.CloudWatchLogHandler(
        log_group=log_group_name,
        stream_name=stream_name,
        log_group_retention_days=30,
        use_queues=cw_use_queues
    )
    cw_logger.setFormatter(formatter)
    logger.addHandler(cw_logger)

    # Don't log to stdout with AWS Lambda. As AWS Lambda adds its own handler to the default logger instance.
    if not 'AWS_LAMBDA_LOG_GROUP_NAME' in os.environ:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)

    return logger