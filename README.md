# sage-hackathon-climate-3-2025
This repository is for Sage Hackathon Climate team 3 in 2025.

## Tools Used

- **FastAPI** – Python web framework for building APIs
- **Uvicorn** – ASGI server for running FastAPI apps
- **boto3** – AWS SDK for Python (used for DynamoDB and S3 access)
- **LocalStack** – Local AWS cloud stack for development and testing
- **Docker & Docker Compose** – Containerization and orchestration
- **Python** – Main programming language

## Setup Instructions

- **setup.sh**  
  Installs Python dependencies, starts LocalStack and other services, and sets up AWS resources in LocalStack.
  
  ```bash
  chmod +x setup.sh
  ./setup.sh
  ```

- **restart.sh**  
  Stops all Docker Compose services, rebuilds all images without using the cache, and restarts the services in detached mode.
  
  ```bash
  chmod +x restart.sh
  ./restart.sh
  ```

## API Documentation

- **Backend Swagger UI:**  
  After starting the backend, visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

## AWS CLI Config for LocalStack

To avoid credential errors when using the AWS CLI with LocalStack, add the following to your `~/.aws/credentials` file:

```
[localstack]
aws_access_key_id = test
aws_secret_access_key = test
```

And in your `~/.aws/config` file:

```
[default]
region = us-east-1
output = json
```

This will allow you to use the AWS CLI with LocalStack without real AWS credentials.

## LocalStack S3 Bucket Test

To test S3 bucket access via LocalStack, you can use the AWS CLI:

```bash
aws --endpoint-url=http://localhost:4566 s3 ls --profile localstack
aws --endpoint-url=http://localhost:4566 s3 mb s3://my-localstack-bucket --profile localstack
aws --endpoint-url=http://localhost:4566 s3 cp test.txt s3://my-localstack-bucket/ --profile localstack
aws --endpoint-url=http://localhost:4566 s3 ls s3://my-localstack-bucket/ --profile localstack
```

Or, you can access the file URL if you want to download uploaded file.
```
http://localhost:4566/my-localstack-bucket/<you-file-name>
```

