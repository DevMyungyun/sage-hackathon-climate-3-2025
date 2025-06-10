import boto3
import os

LOCALSTACK_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")

def create_s3_bucket(bucket_name):
    s3 = boto3.client('s3', endpoint_url=LOCALSTACK_ENDPOINT)
    s3.create_bucket(Bucket=bucket_name)
    print(f'S3 Bucket created: {bucket_name}')

def create_dynamodb_table(table_name):
    dynamodb = boto3.client('dynamodb', endpoint_url=LOCALSTACK_ENDPOINT)
    dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    print(f'DynamoDB Table created: {table_name}')

def create_api_gateway(api_name):
    apigateway = boto3.client('apigateway', endpoint_url=LOCALSTACK_ENDPOINT)
    response = apigateway.create_rest_api(
        name=api_name,
        description='API Gateway for LocalStack project'
    )
    print(f'API Gateway created: {api_name}')
    return response['id']

def setup_resources():
    
    create_s3_bucket('my-localstack-bucket')
    create_dynamodb_table('my-localstack-table')
    api_id = create_api_gateway('MyLocalStackAPI')

if __name__ == '__main__':
    setup_resources()