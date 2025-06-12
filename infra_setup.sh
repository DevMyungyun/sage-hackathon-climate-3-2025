#!/bin/bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:4566

set -e

echo "Checking if Docker Compose is already running..."
if docker compose ps | grep 'Up' > /dev/null; then
  echo "Docker Compose is already running. Restarting containers..."
  docker compose down
fi

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Starting LocalStack with Docker Compose..."
docker compose build #--no-cache
docker-compose up -d

echo "Waiting for LocalStack to be ready..."
until curl -s http://localhost:4566/health | grep 'NoSuchBucket' > /dev/null; do
  sleep 2
done

echo "Setting up AWS resources in LocalStack..."
python localstack/scripts/setup_resources.py

echo "Setup complete!"