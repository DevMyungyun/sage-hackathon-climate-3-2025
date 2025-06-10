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

You can install aws by using the following command if it’s not already installed.
```
pip install awscli
```

Configuring an endpoint URL
You can use AWS CLI with an endpoint URL by configuring test environment variables and include the --endpoint-url=<localstack-url> flag in your aws CLI commands. For example:
```
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="us-east-1"

aws --endpoint-url=http://localhost:4566 s3 ls
```

## LocalStack S3 Bucket Test

To test S3 bucket access via LocalStack, you can use the AWS CLI:

```bash
aws --endpoint-url=http://localhost:4566 s3 ls
aws --endpoint-url=http://localhost:4566 s3 mb s3://my-localstack-bucket
aws --endpoint-url=http://localhost:4566 s3 cp test.txt s3://my-localstack-bucket/
aws --endpoint-url=http://localhost:4566 s3 ls s3://my-localstack-bucket/
```

Or, you can access the file URL if you want to download uploaded file.
```
http://localhost:4566/<bucket-name>/<your-file-name>
```

