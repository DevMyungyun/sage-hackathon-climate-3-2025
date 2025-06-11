#!/bin/bash

echo "Select Lambda runtime:"
options=(
  "nodejs22.x"
  "nodejs20.x"
  "nodejs18.x"
  "python3.13"
  "python3.12"
  "python3.11"
  "python3.10"
  "python3.9"
  "java21"
  "java17"
  "java11"
  "java8.al2"
  "dotnet9"
  "dotnet8"
  "ruby3.4"
  "ruby3.3"
  "ruby3.2"
  "provided.al2023"
  "provided.al2"
)
select opt in "${options[@]}"; do
  if [[ -n "$opt" ]]; then
    RUNTIME="$opt"
    break
  else
    echo "Invalid option. Please try again."
  fi
done

echo "Available zip files in ./lambda_workspace:"
zip_files=()
i=1
for f in ./lambda_workspace/*.zip; do
  fname=$(basename "$f")
  zip_files+=("$fname")
  echo "$i) $fname"
  ((i++))
done

while true; do
  read -p "Select a zip file by number: " zip_choice
  if [[ "$zip_choice" =~ ^[0-9]+$ ]] && (( zip_choice >= 1 && zip_choice < i )); then
    ZIP_FILE="${zip_files[$((zip_choice-1))]}"
    break
  else
    echo "Invalid selection. Please choose a valid number."
  fi
done

read -p "Enter Lambda function name: " FUNCTION_NAME
read -p "Enter handler (leave blank for no handler): " HANDLER
read -p "Enter IAM role ARN (press Enter to use default arn:aws:iam::000000000000:role/lambda-role): " ROLE_ARN
if [[ -z "$ROLE_ARN" ]]; then
  ROLE_ARN="arn:aws:iam::000000000000:role/lambda-role"
fi

# Always ask for _custom_id_ tag and add it to tags
read -p "Enter value for _custom_id_ tag (required for Function URL): " CUSTOM_ID
if [[ -z "$CUSTOM_ID" ]]; then
  echo "Error: _custom_id_ tag is required before creating a Function URL."
  exit 1
fi

read -p "Enter additional tags as JSON (leave blank for none, e.g. {\"key\":\"value\"}): " ADDITIONAL_TAGS

if [[ -z "$ADDITIONAL_TAGS" ]]; then
  TAGS="{\"_custom_id_\":\"$CUSTOM_ID\"}"
else
  # Merge _custom_id_ with additional tags (remove leading/trailing braces if present)
  ADDITIONAL_TAGS_CLEAN=$(echo "$ADDITIONAL_TAGS" | sed 's/^{\(.*\)}$/\1/')
  TAGS="{\"_custom_id_\":\"$CUSTOM_ID\",$ADDITIONAL_TAGS_CLEAN}"
fi

if [[ -z "$HANDLER" ]]; then
  aws --endpoint-url=http://localhost:4566 lambda create-function \
    --function-name "$FUNCTION_NAME" \
    --runtime "$RUNTIME" \
    --zip-file "fileb://$PWD/lambda_workspace/$ZIP_FILE" \
    --role "$ROLE_ARN" \
    --tags "$TAGS" \
    --no-cli-pager
else
  aws --endpoint-url=http://localhost:4566 lambda create-function \
    --function-name "$FUNCTION_NAME" \
    --runtime "$RUNTIME" \
    --zip-file "fileb://$PWD/lambda_workspace/$ZIP_FILE" \
    --handler "$HANDLER" \
    --role "$ROLE_ARN" \
    --tags "$TAGS" \
    --no-cli-pager
fi

echo "Note: You must specify the _custom_id_ tag before creating a Function URL. After the URL configuration is set up, any modifications to the tag will not affect it."