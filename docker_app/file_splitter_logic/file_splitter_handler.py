import os
from datetime import datetime
import logging
from logging.config import fileConfig
from lib.logger import get_logger
from os.path import join
import sys
import csv
import xlsxwriter as xw
import boto3

from lib.settings import ENVIRONMENT, LOG_LEVEL,log_group_name_consumer,request_payload_region,ecr_repository_name,target_bucket,kms_key

fileConfig("resources/logging_config.ini")

logging.getLogger().setLevel(LOG_LEVEL)
logging.info("Preparing parameters")

## For Testing purpose 
bucket_name='anl-vip-dev-s3-input-filesplitter-src'
#file_name='input-file-1.csv'
#file_save_as=file_name.split('.')[0]+'_tmp'+'.'+file_name.split('.')[1]
#kms_key='7912073d-d5ce-4dc7-8034-4ddad9e29ae3'

#tgt_bucket_name = 'anl-vip-dev-s3-input-filesplitter-tgt'


######################

parameters = {
    "ENVIRONMENT": ENVIRONMENT,
    "log_group_name_consumer": log_group_name_consumer,
    "request_payload_region" : request_payload_region,
    "ecr_repository_name" : ecr_repository_name,
    #"source_bucket_name" : source_bucket, 
    "tgt_bucket_name" : target_bucket,
    "kms_key": kms_key
}

#bucket_name = parameters["source_bucket_name"]
tgt_bucket_name = parameters["tgt_bucket_name"]
file_name='input-file-1.csv'
file_save_as=file_name.split('.')[0]+'_tmp'+'.'+file_name.split('.')[1]
kms_key=parameters["kms_key"]

s3_client = boto3.client('s3',region_name='eu-west-1')

def get_dict_list(bucket_name,file_name,file_save_as):
    #s3_client.get_object(Bucket='anl-vip-dev-s3-input-filesplitter-src',Key='input-file-1.csv')
    s3_client.download_file(bucket_name,file_name,file_save_as)
    logging.info('File downloaded successfully ....')
    logging.info(os.listdir('.'))
    #s3_client.put_object()
    list_of_dict_items = []
    with open(file_save_as, encoding="utf8") as f:
        csv_reader = csv.DictReader(f,delimiter=";")
        for line in csv_reader:
            result_dict = dict(line)
            list_of_dict_items.append(result_dict)
        
        return list_of_dict_items
        


def write_to_excel_output(input_dict):
    today_date = datetime.today().strftime('%Y%m%d')
    get_id = input_dict.get('contract_nr')
    output_file_name= str(get_id)+'_'+str(today_date)+'.xlsx'
    logging.info(f'File : {output_file_name}')
    workbook = xw.Workbook(output_file_name)
    worksheet = workbook.add_worksheet()
    col_num = 0
    for key, value in input_dict.items():
        worksheet.write(0, col_num, key)
        worksheet.write(1, col_num, value)
        col_num += 1

    workbook.close()

def write_files_to_s3(bucket_name,kms_key):
    
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for f in files:
        #logging.info(f)
        file_extension = f.split('.')[1]
        if file_extension == 'xlsx':
            object_key = 'tmp/'+ f
            s3_client.upload_file(f,bucket_name,object_key,ExtraArgs={"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": kms_key })
            logging.info(f'File {f} is written successfully ...')


if __name__ == "__main__":
    logging.info("-------------------------- FILE SPLITTER PROCESS BEGINS HERE  -------------------------- ")
    get_list_of_dict = get_dict_list(bucket_name,file_name,file_save_as)
    for item in get_list_of_dict:
        write_to_excel_output(item)
    

    write_files_to_s3(tgt_bucket_name,kms_key)

    logging.info("-------------------------- FILE SPLITTER PROCESS ENDS HERE -------------------------- ")