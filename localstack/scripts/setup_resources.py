import boto3
import os

LOCALSTACK_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")
S3_BUCKET_LIST = ['landing', 'scripts', 'builds']

def create_s3_bucket(bucket_name):
    s3 = boto3.client('s3', endpoint_url=LOCALSTACK_ENDPOINT)
    s3.create_bucket(Bucket=bucket_name)
    print(f'S3 Bucket created: {bucket_name}')


def setup_resources():
    
    for bucket in S3_BUCKET_LIST:
        create_s3_bucket(bucket)


if __name__ == '__main__':
    setup_resources()