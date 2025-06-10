import boto3
import json
import os

LOCALSTACK_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")

# def create_vpc():
#     ec2 = boto3.client('ec2', endpoint_url=LOCALSTACK_ENDPOINT)
#     response = ec2.create_vpc(CidrBlock='10.0.0.0/16')
#     vpc_id = response['Vpc']['VpcId']
#     print(f'VPC created with ID: {vpc_id}')
#     return vpc_id

# def create_iam_role(role_name, policy_document):
#     iam = boto3.client('iam', endpoint_url=LOCALSTACK_ENDPOINT)
#     response = iam.create_role(
#         RoleName=role_name,
#         AssumeRolePolicyDocument=json.dumps(policy_document)
#     )
#     print(f'IAM Role created: {role_name}')
#     return response['Role']['Arn']

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

# This is Paid feature in LocalStack Pro.
# def create_cognito_user_pool(pool_name):
#     cognito = boto3.client('cognito-idp', endpoint_url=LOCALSTACK_ENDPOINT)
#     response = cognito.create_user_pool(
#         PoolName=pool_name
#     )
#     print(f'Cognito User Pool created: {pool_name}')
#     return response['UserPool']['Id']

# def create_subnet(vpc_id, cidr_block, availability_zone):
#     ec2 = boto3.client('ec2', endpoint_url=LOCALSTACK_ENDPOINT)
#     response = ec2.create_subnet(
#         VpcId=vpc_id,
#         CidrBlock=cidr_block,
#         AvailabilityZone=availability_zone
#     )
#     subnet_id = response['Subnet']['SubnetId']
#     print(f'Subnet created: {subnet_id} ({cidr_block})')
#     return subnet_id

# def create_ec2_instance(subnet_id, iam_role_arn, instance_name, user_data=None, key_name='localstack-key', security_group_ids=None):
#     ec2 = boto3.client('ec2', endpoint_url=LOCALSTACK_ENDPOINT)
#     params = {
#         'ImageId': 'ami-12345678',  # Dummy AMI for LocalStack
#         'InstanceType': 't2.micro',
#         'MaxCount': 1,
#         'MinCount': 1,
#         'SubnetId': subnet_id,
#         'IamInstanceProfile': {'Arn': iam_role_arn},
#         'KeyName': key_name,
#         'TagSpecifications': [{
#             'ResourceType': 'instance',
#             'Tags': [{'Key': 'Name', 'Value': instance_name}]
#         }]
#     }
#     if security_group_ids:
#         params['SecurityGroupIds'] = security_group_ids
#     if user_data:
#         params['UserData'] = user_data
#     response = ec2.run_instances(**params)
#     instance_id = response['Instances'][0]['InstanceId']
#     print(f'EC2 Instance created: {instance_id} in subnet {subnet_id}')
#     return instance_id

# def create_instance_profile_and_attach_role(role_name):
#     iam = boto3.client('iam', endpoint_url=LOCALSTACK_ENDPOINT)
#     # Create instance profile
#     try:
#         iam.create_instance_profile(InstanceProfileName=role_name)
#         print(f'Instance profile created: {role_name}')
#     except iam.exceptions.EntityAlreadyExistsException:
#         print(f'Instance profile already exists: {role_name}')
#     # Add role to instance profile
#     try:
#         iam.add_role_to_instance_profile(
#             InstanceProfileName=role_name,
#             RoleName=role_name
#         )
#         print(f'Role {role_name} added to instance profile {role_name}')
#     except iam.exceptions.LimitExceededException:
#         print(f'Role {role_name} already attached to instance profile {role_name}')
#     # Get the instance profile ARN
#     profile = iam.get_instance_profile(InstanceProfileName=role_name)
#     return profile['InstanceProfile']['Arn']

# def create_key_pair(key_name):
#     ec2 = boto3.client('ec2', endpoint_url=LOCALSTACK_ENDPOINT)
#     try:
#         response = ec2.create_key_pair(KeyName=key_name)
#         private_key = response['KeyMaterial']
#         with open(f"{key_name}.pem", "w") as f:
#             f.write(private_key)
#         os.chmod(f"{key_name}.pem", 0o400)
#         print(f"Key pair '{key_name}' created and saved to {key_name}.pem")
#     except ec2.exceptions.ClientError as e:
#         if "InvalidKeyPair.Duplicate" in str(e):
#             print(f"Key pair '{key_name}' already exists.")
#         else:
#             raise

# def create_security_group(vpc_id, group_name, description):
#     ec2 = boto3.client('ec2', endpoint_url=LOCALSTACK_ENDPOINT)
#     response = ec2.create_security_group(
#         GroupName=group_name,
#         Description=description,
#         VpcId=vpc_id
#     )
#     sg_id = response['GroupId']
#     print(f"Security Group created: {sg_id}")

#     # Example: Allow all inbound traffic (for demo; restrict in production)
#     ec2.authorize_security_group_ingress(
#         GroupId=sg_id,
#         IpPermissions=[
#             {
#                 'IpProtocol': 'tcp',
#                 'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
#                 'FromPort': ,
#                 'ToPort': 22
#             }
#         ]
#     )
#     print(f"Ingress rule added to Security Group: {sg_id}")
#     return sg_id

def setup_resources():
    # vpc_id = create_vpc()
    # iam_role_arn = create_iam_role('EC2AccessRole', {
    #     "Version": "2012-10-17",
    #     "Statement": [
    #         {
    #             "Effect": "Allow",
    #             "Principal": {"Service": "ec2.amazonaws.com"},
    #             "Action": "sts:AssumeRole"
    #         }
    #     ]
    # })
    
    # instance_profile_arn = create_instance_profile_and_attach_role('EC2AccessRole')

    create_s3_bucket('my-localstack-bucket')
    create_dynamodb_table('my-localstack-table')
    api_id = create_api_gateway('MyLocalStackAPI')
    # Congnito is a paid feature in LocalStack Pro
    # user_pool_id = create_cognito_user_pool('MyLocalStackUserPool')

    # public_subnet_id = create_subnet(vpc_id, '10.0.1.0/24', 'us-east-1a')
    # private_subnet_id = create_subnet(vpc_id, '10.0.2.0/24', 'us-east-1a')

    # Example user data scripts
#     frontend_user_data = """#!/bin/bash
# echo 'Hello from Frontend!' > /home/ec2-user/frontend.txt
# """
#     backend_user_data = """#!/bin/bash
# echo 'Hello from Backend!' > /home/ec2-user/backend.txt
# """

#     create_key_pair('localstack-key')

#     sg_id = create_security_group(vpc_id, 'localstack-sg', 'LocalStack Security Group')

#     public_instance_id = create_ec2_instance(
#         public_subnet_id, instance_profile_arn, 'FrontendInstance',
#         user_data=frontend_user_data,
#         key_name='localstack-key',
#         security_group_ids=[sg_id]
#     )
#     private_instance_id = create_ec2_instance(
#         private_subnet_id, instance_profile_arn, 'BackendInstance',
#         user_data=backend_user_data,
#         key_name='localstack-key',
#         security_group_ids=[sg_id]
#     )

if __name__ == '__main__':
    setup_resources()