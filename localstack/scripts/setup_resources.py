import boto3
import os

LOCALSTACK_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")

def create_s3_bucket(bucket_name):
    s3 = boto3.client('s3', endpoint_url=LOCALSTACK_ENDPOINT)
    s3.create_bucket(Bucket=bucket_name)
    print(f'S3 Bucket created: {bucket_name}')


def setup_resources():
    
    create_s3_bucket('my-localstack-bucket')

if __name__ == '__main__':
    setup_resources()