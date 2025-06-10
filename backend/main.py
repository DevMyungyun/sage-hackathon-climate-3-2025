from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # Remove if you don't want CORS
import boto3
import uuid
import os

app = FastAPI()

# Uncomment below to enable CORS (remove if you want CORS disabled)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# AWS LocalStack configuration
DYNAMODB_ENDPOINT_URL = os.environ.get("DYNAMODB_ENDPOINT_URL", "http://localhost:4566")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "my-localstack-table")
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:4566")
S3_BUCKET = os.environ.get("S3_BUCKET", "my-localstack-bucket")

session = boto3.Session(
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1"
)
dynamodb = session.resource("dynamodb", endpoint_url=DYNAMODB_ENDPOINT_URL)
s3 = session.resource("s3", endpoint_url=S3_ENDPOINT_URL)

def ensure_table():
    existing_tables = dynamodb.meta.client.list_tables()["TableNames"]
    if DYNAMODB_TABLE_NAME not in existing_tables:
        table = dynamodb.create_table(
            TableName=DYNAMODB_TABLE_NAME,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        table.wait_until_exists()

@app.on_event("startup")
def startup_event():
    ensure_table()

@app.get("/api/todos")
def get_todos():
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
    response = table.scan()
    return response.get("Items", [])

@app.post("/api/todos")
def create_todo(data: dict):
    todo_id = str(uuid.uuid4())
    item = {
        "id": todo_id,
        "task": data.get("task"),
        "done": False
    }
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
    table.put_item(Item=item)
    return JSONResponse(item, status_code=201)

@app.put("/api/todos/{todo_id}")
def update_todo(todo_id: str, data: dict):
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
    response = table.update_item(
        Key={"id": todo_id},
        UpdateExpression="SET task = :t, done = :d",
        ExpressionAttributeValues={":t": data.get("task"), ":d": data.get("done")},
        ReturnValues="ALL_NEW"
    )
    return response.get("Attributes", {})

@app.delete("/api/todos/{todo_id}")
def delete_todo(todo_id: str):
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
    table.delete_item(Key={"id": todo_id})
    return JSONResponse(content="", status_code=204)

@app.post("/api/upload")
def upload_file(file: UploadFile = File(...)):
    s3.Bucket(S3_BUCKET).put_object(Key=file.filename, Body=file.file)
    return {"message": f"Uploaded {file.filename} to S3"}

# To run: uvicorn app:app --host 0.0.0.0 --port 8000