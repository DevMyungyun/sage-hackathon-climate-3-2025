#!/bin/bash

echo "Fetching existing Lambda functions..."
functions=($(aws --endpoint-url=http://localhost:4566 lambda list-functions --query 'Functions[*].FunctionName' --output text))

if [ ${#functions[@]} -eq 0 ]; then
  echo "No Lambda functions found."
  exit 1
fi

echo "Select a Lambda function to invoke:"
select FUNCTION_NAME in "${functions[@]}"; do
  if [[ -n "$FUNCTION_NAME" ]]; then
    break
  else
    echo "Invalid selection. Please choose a valid number."
  fi
done

read -p "Enter payload as JSON (e.g., '{\"body\": \"{\\\"num1\\\": \\\"10\\\", \\\"num2\\\": \\\"10\\\"}\" }'): " PAYLOAD
read -p "Enter output file name (e.g., output.txt): " OUTPUT_FILE

aws --endpoint-url=http://localhost:4566 lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --cli-binary-format raw-in-base64-out \
    --payload "$PAYLOAD" \
    ./lambda_workspace/output/"$OUTPUT_FILE"

echo "Invocation complete. Output saved to ./lambda_workspace/output/$OUTPUT_FILE"