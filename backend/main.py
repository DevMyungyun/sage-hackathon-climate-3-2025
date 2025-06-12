from fastapi import FastAPI, HTTPException, UploadFile, File, Response, Form, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # Remove if you don't want CORS disabled
from pymongo import MongoClient
from fastapi.encoders import jsonable_encoder

import boto3
import os
import logging
import requests
from datetime import datetime
import pandas as pd
import io
import math

app = FastAPI(
    title="Sage Hackathon Climate 3 API",
    description="API documentation for Sage Hackathon Climate 3 backend (FastAPI, S3, MongoDB)",
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

# MongoDB configuration with authentication
MONGODB_ENDPOINT = os.environ.get("MONGODB_ENDPOINT", "mongodb://mongodb:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", "testdb")
MONGODB_COLLECTION = os.environ.get("MONGODB_COLLECTION", "testcollection")
MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME", "")
MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD", "")

SYNC_WEBHOOK_URL = os.environ.get("SYNC_WEBHOOK_URL", "http://sync-webhook:9000")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

s3 = session.resource("s3", endpoint_url=S3_ENDPOINT)

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
        # Try listing collections to check connection
        mongo_db.list_collection_names()
        logging.info(f"[SUCCESS] Connected to MongoDB at {MONGODB_ENDPOINT}")
    except Exception as e:
        logging.error(f"[FAIL] Could not connect to MongoDB at {MONGODB_ENDPOINT}: {e}")

# REST APIs 
@app.post("/api/s3/{bucket_name}/upload")
def upload_file_to_bucket(
    bucket_name: str,
    file: UploadFile = File(...),
    region: str = Query(..., description="Region name"),
    station: str = Query(..., description="Station name")
):
    """
    Upload a file to the specified S3 bucket, including region and station metadata.
    Only allows CSV or Excel files for the 'landing' bucket.
    Only allows R script files (.R or .r) for the 'scripts' bucket.
    """
    # Only allow CSV or Excel files for the 'landing' bucket
    if bucket_name == "landing":
        allowed_types = [
            "text/csv"
        ]
        allowed_exts = [".csv"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file.content_type not in allowed_types and file_ext not in allowed_exts:
            raise HTTPException(
                status_code=400,
                detail="Only CSV or Excel files are allowed for the 'landing' bucket."
            )
        # Change filename to filename-yyyymmddhhmmss.ext
        base, ext = os.path.splitext(file.filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        upload_filename = f"{base}-{timestamp}{ext}"
    else:
        upload_filename = file.filename

    # Only allow R script files for the 'scripts' bucket
    if bucket_name == "scripts":
        allowed_exts = [".r", ".R"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_exts:
            raise HTTPException(
                status_code=400,
                detail="Only R script files (.R or .r) are allowed for the 'scripts' bucket."
            )

    bucket = get_bucket(bucket_name)
    s3_key = f"{region}/{station}/climsoft/{upload_filename}"
    bucket.put_object(Key=s3_key, Body=file.file, Metadata={"region": region, "station": station})

    # After successful upload, trigger sync-webhook
    try:
        webhook_url = f"{SYNC_WEBHOOK_URL}/api/webhook/{bucket_name}/sync"
        params = {"region": region, "station": station}
        response = requests.post(webhook_url, params=params, timeout=10)
        response.raise_for_status()
        webhook_result = response.json()
    except Exception as e:
        webhook_result = {"error": f"Failed to trigger sync-webhook: {e}"}

    return {
        "message": f"Uploaded {upload_filename} to {bucket_name} at {region}/{station}/",
        "webhook_result": webhook_result
    }

@app.get("/api/s3/{bucket_name}/download/{filename}")
def download_file_from_bucket(
    bucket_name: str,
    filename: str,
    region: str = Query(..., description="Region name"),
    station: str = Query(..., description="Station name")
):
    """
    Download a file from the specified S3 bucket and region/station path.
    """
    s3_key = f"{region}/{station}/climsoft/{filename}"
    bucket = get_bucket(bucket_name)
    try:
        obj = bucket.Object(s3_key).get()
        content = obj['Body'].read()
        return Response(
            content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found in {bucket_name} at {s3_key}: {e}")

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


@app.get("/api/s3/builds/latest-climate-data")
def get_latest_builds_csv_as_json(
    region: str = Query(..., description="Region name"),
    station: str = Query(..., description="Station name")
):
    """
    Download the latest CSV file in the builds S3 bucket for the given region/station,
    read it, convert to JSON, and return the data.
    """
    builds_bucket = get_bucket("builds")
    prefix = f"{region}/{station}/climsoft/"
    csv_files = [
        obj for obj in builds_bucket.objects.filter(Prefix=prefix)
        if obj.key.endswith(".csv")
    ]
    if not csv_files:
        raise HTTPException(status_code=404, detail="No CSV files found in builds bucket for this region/station.")

    latest_obj = max(csv_files, key=lambda obj: obj.last_modified)
    obj = builds_bucket.Object(latest_obj.key).get()
    content = obj['Body'].read()

    try:
        df = pd.read_csv(io.BytesIO(content))
        # Replace NaN and inf/-inf with None for JSON compliance
        def clean_value(x):
            if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
                return None
            return x
        data = df.applymap(clean_value).to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading CSV: {e}")

    return {"filename": latest_obj.key, "data": data}


# TODO: This is for future features to interact with MongoDB
@app.get("/api/todos/find")
def find_documents():
    """Find all documents in MongoDB collection."""
    docs = list(mongo_collection.find())
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs

@app.get("/api/todos")
def get_todos():
    docs = list(mongo_collection.find())
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs

@app.post("/api/todos/insert")
def insert_document(document: dict):
    """Insert a document into MongoDB."""
    result = mongo_collection.insert_one(document)
    return {"inserted_id": str(result.inserted_id)}

@app.delete("/api/todos/{todo_id}")
def delete_todo(todo_id: str):
    result = mongo_collection.delete_one({"id": todo_id})
    if result.deleted_count == 1:
        return JSONResponse(content="", status_code=204)
    raise HTTPException(status_code=404, detail="Todo not found")


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

def get_bucket(bucket_name: str):
    if bucket_name not in S3_BUCKETS:
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' not allowed")
    return s3.Bucket(bucket_name)
