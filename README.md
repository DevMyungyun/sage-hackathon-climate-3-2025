# sage-hackathon-climate-3-2025
This repository is for Sage Hackathon Climate team 3 in 2025.

## Bucket Structure

The platform will need three main buckets:
- **landing** – storing raw dataset files. It should have the following structure: 

`landing > country_name > district > source`

- **scripts** – storing R scripts.
- **build** – storing processed dataset after been transformed by the R scripts. It should have the following structure:

`build > country_name > district > source`

## Naming Conventions

- Dataset naming should have (at least) the date when it was exported following the pattern `YYYY-MM-DD`.
- R script naming has to be match with `country name-YYYY-version.R(or .r)` pattern. The example name is like this `Malawi-2023-v1.R`.
- Processed dataset should have (at least) the date when it was processed and the script name following the pattern `YYYY-MM-DD_COUNTRY-YEAR-VERSION`. The example name is like this `YYYY-MM-DD_Malawi-2023-v1.R`.

## Tools Used

- **FastAPI** – Python web framework for building APIs
- **Uvicorn** – ASGI server for running FastAPI apps
- **boto3** – AWS SDK for Python (used for DynamoDB and S3 access)
- **LocalStack** – Local AWS cloud stack for development and testing
- **Docker & Docker Compose** – Containerization and orchestration
- **Python** – Main programming language

## Setup Instructions

#### Docker

Verify you have docker installed and the docker daemon running.

To install docker, use https://www.docker.com/get-started/ documentation.


#### Python environment

It's also recommended to use a Python virtual environment.

Python virtual environments documentation https://docs.python.org/3/library/venv.html.

#### AWS CLI Config for LocalStack

You can install aws by using the following command if it’s not already installed.
```
pip install awscli
```

#### Configuring an endpoint URL in infra_setup

In the infra_setup.sh file you can configure test environment variables.

```
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ENDPOINT_URL=http://localhost:4566
```

Use AWS CLI with an endpoint URL including the --endpoint-url=<localstack-url> flag in your AWS CLI commands. (Mac/Linux) example:

```bash
aws --endpoint-url=http://localhost:4566 s3 ls
```

#### Configuration files (_MAC/Linux_)

- **infra_setup.sh**  
  Installs Python dependencies, starts LocalStack and other services, and sets up AWS resources in LocalStack.
  
  ```bash
  chmod +x infra_setup.sh
  ./infra_setup.sh
  ```

#### LocalStack S3 Bucket Test

To test S3 bucket access via LocalStack, you can use the AWS CLI:

List S3 bucket content. Spoiler alert: will return nothing because the bucket is empty.
```bash
aws --endpoint-url=http://localhost:4566 s3 ls
```

Let's create a bucket.
```bash
aws --endpoint-url=http://localhost:4566 s3 mb s3://my-localstack-bucket
```

And add a file (just for testing purposes).
```bash
aws --endpoint-url=http://localhost:4566 s3 cp requirements.txt s3://my-localstack-bucket/
```

Let's list the bucket again, it should show the bucket and file created before.
```bash
aws --endpoint-url=http://localhost:4566 s3 ls s3://my-localstack-bucket/
```

Or, you can access the file URL if you want to download uploaded file using http://localhost:4566/<bucket-name>/<your-file-name>.
```
http://localhost:4566/my-localstack-bucket/requirements.txt
```

## API Documentation

- **Backend Swagger UI:**  
  After starting the backend, visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

- **Sync Webhook Swagger UI:**  
  After starting the backend, visit [http://localhost:9000/docs](http://localhost:8000/docs) for interactive API documentation.

## Additional Tool for Localstack 

- **create_lambda_func.sh**  
  Interactive script to create a Lambda function in LocalStack.  
  It lets you select runtime, zip file (from `./lambda_workspace`), handler, role, and tags (including required `_custom_id_`). You can place your archive the code to zip file under `./lambda_workspace` folder. This script will pick up your created zip file.

  ```bash
  chmod +x lambda_func_create.sh
  ./lambda_func_create.sh 
  ```
  Output
  ```
  Select Lambda runtime:
  1) nodejs22.x         8) python3.9        15) ruby3.4
  2) nodejs20.x         9) java21           16) ruby3.3
  3) nodejs18.x        10) java17           17) ruby3.2
  4) python3.13        11) java11           18) provided.al2023
  5) python3.12        12) java8.al2        19) provided.al2
  6) python3.11        13) dotnet9
  7) python3.10        14) dotnet8
  #? 3
  Available zip files in ./lambda_workspace:
  1) test01_1.zip
  2) test01.zip
  3) test02.zip
  Select a zip file by number: 2
  Enter Lambda function name: test01
  Enter handler (leave blank for no handler): index.handler
  Enter IAM role ARN (press Enter to use default arn:aws:iam::000000000000:role/lambda-role): 
  Enter value for _custom_id_ tag (required for Function URL): test01
  Enter additional tags as JSON (leave blank for none, e.g. {"key":"value"}): 
  {
      "FunctionName": "test01",
      "FunctionArn": "arn:aws:lambda:us-east-1:000000000000:function:test01",
      "Runtime": "nodejs18.x",
      ...
      }
  }
  Note: You must specify the _custom_id_ tag before creating a Function URL. After the URL configuration is set up, any modifications to the tag will not affect it.
  ```

- **update_lambda_func_code.sh**  
  Interactive script to update Lambda function code in LocalStack.  
  Lets you select an existing Lambda function, choose or create a zip file from `./lambda_zip`, and uploads it.

  ```bash
  chmod +x lambda_func_code_update.sh
  ./lambda_func_code_update.sh
  ```
  Output:
  ```
  ./update_lambda_func_code.sh 
  Fetching existing Lambda functions...
  Select a Lambda function to update:
  1) test01
  #? 1
  Do you want to use an existing zip file or create a new one from a file/folder?
  1) Use existing zip
  2) Create new zip from file/folder
  #? 2
  Available files and folders in ./lambda_zip (excluding .zip files):
  1) index.js
  Select a file or folder by number to zip: 1
  Enter the name for the new zip file (e.g., my-function.zip): test01_1.zip
    adding: index.js (deflated 39%)
  Created zip file ./lambda_zip/test01_1.zip from index.js.
  ```

- **lambda_func_invoke.sh**  
  Interactive script to invoke a Lambda function in LocalStack.  
  Lets you select a function, enter a payload, and specify an output file.

  ```bash
  chmod +x lambda_func_invoke.sh
  ./lambda_func_invoke.sh
  ```
  Output:
  ```
  ./lambda_func_invoke.sh
  Fetching existing Lambda functions...
  Select a Lambda function to invoke:
  1) test01
  #? 1
  Enter payload as JSON (e.g., '{"body": "{\"num1\": \"10\", \"num2\": \"10\"}" }'): '{"body": "{\"num1\": \"10\", \"num2\": \"10\"}" }'
  Enter output file name (e.g., output.txt): output_01.json
  ```
