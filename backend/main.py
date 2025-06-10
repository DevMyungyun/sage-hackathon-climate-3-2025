from fastapi import FastAPI, HTTPException, UploadFile, File, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # Remove if you don't want CORS disabled
from elasticsearch import Elasticsearch, exceptions as es_exceptions
from pymongo import MongoClient

import boto3
import uuid
import os
import logging

app = FastAPI(
    title="Sage Hackathon Climate 3 API",
    description="API documentation for Sage Hackathon Climate 3 backend (FastAPI, S3, MongoDB, Elasticsearch)",
    version="1.0.0"
)

# Uncomment below to enable CORS (remove if you want CORS disabled)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# AWS LocalStack configuration
S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://localstack:4566")
S3_BUCKETS = os.environ.get("S3_BUCKETS", "landing,scripts,builds").split(",")

session = boto3.Session(
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)

# Elasticsearch configuration with authentication
ELASTICSEARCH_ENDPOINT = os.environ.get("ELASTICSEARCH_ENDPOINT", "http://elasticsearch:9200")
ELASTICSEARCH_USERNAME = os.environ.get("ELASTICSEARCH_USERNAME", "")
ELASTICSEARCH_PASSWORD = os.environ.get("ELASTICSEARCH_PASSWORD", "")

# MongoDB configuration with authentication
MONGODB_ENDPOINT = os.environ.get("MONGODB_ENDPOINT", "mongodb://mongodb:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", "testdb")
MONGODB_COLLECTION = os.environ.get("MONGODB_COLLECTION", "testcollection")
MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME", "")
MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

s3 = session.resource("s3", endpoint_url=S3_ENDPOINT)

if ELASTICSEARCH_USERNAME and ELASTICSEARCH_PASSWORD:
    es = Elasticsearch(
        [ELASTICSEARCH_ENDPOINT],
        basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
        verify_certs=False
    )
else:
    es = Elasticsearch([ELASTICSEARCH_ENDPOINT])

if MONGODB_USERNAME and MONGODB_PASSWORD:
    # Insert credentials into the URI if not already present
    if "@" not in MONGODB_ENDPOINT:
        mongo_uri = MONGODB_ENDPOINT.replace("mongodb://", f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@")
    else:
        mongo_uri = MONGODB_ENDPOINT
    mongo_client = MongoClient(mongo_uri)
else:
    mongo_client = MongoClient(MONGODB_ENDPOINT)
mongo_db = mongo_client[MONGODB_DB]
mongo_collection = mongo_db[MONGODB_COLLECTION]

@app.on_event("startup")
async def startup_event():
    # Service connection checks with logging
    try:
        # Try listing buckets to check connection
        list(s3.buckets.all())
        logging.info(f"[SUCCESS] Connected to S3 at {S3_ENDPOINT}")
    except Exception as e:
        logging.error(f"[FAIL] Could not connect to S3 at {S3_ENDPOINT}: {e}")

    try:
        # Try pinging Elasticsearch
        if es.ping():
            logging.info(f"[SUCCESS] Connected to Elasticsearch at {ELASTICSEARCH_ENDPOINT}")
        else:
            logging.error(f"[FAIL] Could not connect to Elasticsearch at {ELASTICSEARCH_ENDPOINT}: ping failed")
    except es_exceptions.ElasticsearchException as e:
        logging.error(f"[FAIL] Could not connect to Elasticsearch at {ELASTICSEARCH_ENDPOINT}: {e}")

    try:
        # Try listing collections to check connection
        mongo_db.list_collection_names()
        logging.info(f"[SUCCESS] Connected to MongoDB at {MONGODB_ENDPOINT}")
    except Exception as e:
        logging.error(f"[FAIL] Could not connect to MongoDB at {MONGODB_ENDPOINT}: {e}")

# REST APIs 
@app.get("/api/todos")
def get_todos():
    docs = list(mongo_collection.find())
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs

@app.post("/api/todos")
def create_todo(data: dict):
    todo_id = str(uuid.uuid4())
    item = {
        "id": todo_id,
        "task": data.get("task"),
        "done": False
    }
    result = mongo_collection.insert_one(item)
    item["_id"] = str(result.inserted_id)
    return JSONResponse(item, status_code=201)

@app.put("/api/todos/{todo_id}")
def update_todo(todo_id: str, data: dict):
    result = mongo_collection.find_one_and_update(
        {"id": todo_id},
        {"$set": {"task": data.get("task"), "done": data.get("done")}},
        return_document=True
    )
    if result:
        result["_id"] = str(result["_id"])
        return result
    raise HTTPException(status_code=404, detail="Todo not found")

@app.delete("/api/todos/{todo_id}")
def delete_todo(todo_id: str):
    result = mongo_collection.delete_one({"id": todo_id})
    if result.deleted_count == 1:
        return JSONResponse(content="", status_code=204)
    raise HTTPException(status_code=404, detail="Todo not found")

@app.post("/api/es/index")
def index_document(index: str, document: dict):
    """Index a document into Elasticsearch."""
    response = es.index(index=index, document=document)
    return {"result": response["result"], "id": response["_id"]}

@app.get("/api/es/search")
def search_documents(index: str, query: dict):
    """Search documents in Elasticsearch."""
    response = es.search(index=index, query=query)
    return response["hits"]["hits"]

@app.post("/api/mongo/insert")
def insert_document(document: dict):
    """Insert a document into MongoDB."""
    result = mongo_collection.insert_one(document)
    return {"inserted_id": str(result.inserted_id)}

@app.get("/api/mongo/find")
def find_documents():
    """Find all documents in MongoDB collection."""
    docs = list(mongo_collection.find())
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs

def get_bucket(bucket_name: str):
    if bucket_name not in S3_BUCKETS:
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' not allowed")
    return s3.Bucket(bucket_name)

@app.post("/api/s3/{bucket_name}/upload")
def upload_file_to_bucket(bucket_name: str, file: UploadFile = File(...)):
    bucket = get_bucket(bucket_name)
    bucket.put_object(Key=file.filename, Body=file.file)
    return {"message": f"Uploaded {file.filename} to {bucket_name}"}

@app.get("/api/s3/{bucket_name}/download/{filename}")
def download_file_from_bucket(bucket_name: str, filename: str):
    bucket = get_bucket(bucket_name)
    try:
        obj = bucket.Object(filename).get()
        content = obj['Body'].read()
        return Response(
            content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found in {bucket_name}: {e}")

@app.get("/api/s3/{bucket_name}/read")
def list_files_in_bucket(bucket_name: str):
    """
    List all files in the specified S3 bucket.
    """
    bucket = get_bucket(bucket_name)
    try:
        files = [obj.key for obj in bucket.objects.all()]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not list files in {bucket_name}: {e}")

# To run: uvicorn app:app --host 0.0.0.0 --port 8000