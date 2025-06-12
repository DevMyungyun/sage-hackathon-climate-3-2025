from fastapi import FastAPI, HTTPException, UploadFile, File, Response, Form, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # Remove if you don't want CORS disabled
from pymongo import MongoClient

import boto3
import os
import logging
import re
from datetime import datetime
import subprocess
import tempfile
import pandas as pd
import io  # Add this import

app = FastAPI(
    title="Sage Hackathon Climate 3 API",
    description="API documentation for Sage Hackathon Climate 3 sync-webhook (FastAPI, S3, MongoDB)",
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
@app.post("/api/webhook/{bucket_name}/sync")
def sync_file_to_bucket(
    region: str = Query(..., description="Region name"),
    station: str = Query(..., description="Station name")
):
    """
    1. Find the latest R script for the region in the 'scripts' bucket (region-yyyy-vN.R or .r).
    2. Read all files under /region/station/climsoft/ in the 'landing' bucket.
    3. Process the contents using the R script.
    4. Store the result in the 'builds' bucket under /region/station/climsoft/.
    5. Integrate all CSV files in landing bucket and upload the integrated file to both builds and landing buckets.
    """
    # 1. Find the latest R script for the region in '/region/station/climsoft/' in the 'scripts' bucket
    scripts_bucket = get_bucket("scripts")
    prefix_script = f"{region}/{station}/climsoft/"
    pattern = re.compile(rf"^{re.escape(prefix_script)}{re.escape(region)}-(\d{{4}})-v(\d+)\.r$", re.IGNORECASE)
    latest_script = None
    latest_year = -1
    latest_version = -1

    for obj in scripts_bucket.objects.filter(Prefix=prefix_script):
        match = pattern.match(obj.key)
        if match:
            year = int(match.group(1))
            version = int(match.group(2))
            if (year > latest_year) or (year == latest_year and version > latest_version):
                latest_year = year
                latest_version = version
                latest_script = obj.key

    if not latest_script:
        raise HTTPException(status_code=404, detail=f"No R script found for region '{region}' in scripts bucket under {prefix_script}")

    # Download the R script to a temp file in /tmp directory
    script_obj = scripts_bucket.Object(latest_script).get()
    r_script_content = script_obj['Body'].read().decode("utf-8")
    r_script_path = f"/tmp/{os.path.basename(latest_script)}"
    with open(r_script_path, "w") as r_script_file:
        r_script_file.write(r_script_content)

    # 2. Read latest uploaded files under /region/station/climsoft/ in 'landing' bucket. and download the /tmp/latest_dataset.csv file
    landing_bucket = get_bucket("landing")
    prefix_landing = f"{region}/{station}/climsoft/"
    csv_contents = []
    for obj in landing_bucket.objects.filter(Prefix=prefix_landing):
        if obj.key.endswith(".csv"):
            file_content = obj.get()['Body'].read()
            csv_contents.append(file_content)

    if not csv_contents:
        raise HTTPException(status_code=404, detail=f"No CSV files found in landing bucket for region '{region}' and station '{station}'")
    logging.info(f"Found {len(csv_contents)} CSV files in landing bucket for {region}/{station}")
    
    # download the latest dataset CSV file as latest_dataset.csv
    latest_dataset_path = "/tmp/latest_dataset.csv"
    with open(latest_dataset_path, "wb") as f:
        f.write(csv_contents[0])
    logging.info(f"Downloaded latest dataset CSV to {latest_dataset_path}") 

    # 3. Process the integrated /tmp/latest_dataset.csv using the R script placed in r_script_path variable
    try:
        # Create a temporary directory for R script execution
        with tempfile.TemporaryDirectory() as temp_dir:
            result_file = os.path.join(temp_dir, "processed_dataset.csv")
            subprocess.run(["Rscript", r_script_path, latest_dataset_path, result_file], check=True)
            with open(result_file, "rb") as f:
                result_content = f.read()
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"R script execution failed: {e}")
    
    # 5. Store the /tmp/processed_dataset.csv file renaming dataset_update_yyyymmddhhmmss in 'builds' bucket under /region/station/climsoft/
    builds_bucket = get_bucket("builds")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    processed_filename = f"dataset_update_{timestamp}.csv"
    processed_key = f"{region}/{station}/climsoft/{processed_filename}"
    builds_bucket.put_object(Key=processed_key, Body=result_content)
    
    # Delete the /tmp/processed_dataset.csv, /tmp/latest_dataset.csv, and r_script_path files
    os.remove(r_script_path)
    os.remove(latest_dataset_path)
    logging.info(f"Processed dataset saved to builds bucket as {processed_key}")
    
    # Return the response with processed file information
    logging.info(f"Processed files for {region}/{station} and stored in builds bucket as {processed_key}")
    logging.info(f"Using R script: {latest_script}")        

    return JSONResponse(
        content={
            "message": f"Processed files for {region}/{station} and stored in builds bucket.",
            "processed_file": processed_key,
            "script_used": latest_script
        },
        status_code=200
    )

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

# TODO: This is for future features
@app.post("/api/mongo/insert")
def insert_document(document: dict):
    """Insert a document into MongoDB."""
    result = mongo_collection.insert_one(document)
    return {"inserted_id": str(result.inserted_id)}

def get_bucket(bucket_name: str):
    if bucket_name not in S3_BUCKETS:
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' not allowed")
    return s3.Bucket(bucket_name)
