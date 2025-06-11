#!/bin/bash

echo "Fetching existing Lambda functions..."
functions=($(aws --endpoint-url=http://localhost:4566 lambda list-functions --query 'Functions[*].FunctionName' --output text))

if [ ${#functions[@]} -eq 0 ]; then
  echo "No Lambda functions found."
  exit 1
fi

echo "Select a Lambda function to update:"
select FUNCTION_NAME in "${functions[@]}"; do
  if [[ -n "$FUNCTION_NAME" ]]; then
    break
  else
    echo "Invalid selection. Please choose a valid number."
  fi
done

echo "Do you want to use an existing zip file or create a new one from a file/folder?"
select zip_option in "Use existing zip" "Create new zip from file/folder"; do
  if [[ "$zip_option" == "Use existing zip" ]]; then
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

    read -p "Enter the name you want for the zip file to upload (e.g., my-function.zip): " FINAL_ZIP_NAME
    if [[ "$ZIP_FILE" != "$FINAL_ZIP_NAME" ]]; then
      cp "./lambda_workspace/$ZIP_FILE" "./lambda_workspace/$FINAL_ZIP_NAME"
      ZIP_FILE="$FINAL_ZIP_NAME"
      echo "Copied $ZIP_FILE to $FINAL_ZIP_NAME for upload."
    fi
    break

  elif [[ "$zip_option" == "Create new zip from file/folder" ]]; then
    echo "Available files and folders in ./lambda_workspace (excluding .zip files):"
    non_zip_files=()
    i=1
    for f in ./lambda_workspace/*; do
      if [[ ! "$f" =~ \.zip$ ]]; then
        fname=$(basename "$f")
        non_zip_files+=("$fname")
        echo "$i) $fname"
        ((i++))
      fi
    done

    if [ ${#non_zip_files[@]} -eq 0 ]; then
      echo "No non-zip files or folders found in ./lambda_workspace."
      exit 1
    fi

    while true; do
      read -p "Select a file or folder by number to zip: " file_choice
      if [[ "$file_choice" =~ ^[0-9]+$ ]] && (( file_choice >= 1 && file_choice < i )); then
        SELECTED_FILE="${non_zip_files[$((file_choice-1))]}"
        break
      else
        echo "Invalid selection. Please choose a valid number."
      fi
    done

    read -p "Enter the name for the new zip file (e.g., my-function.zip): " FINAL_ZIP_NAME
    (cd ./lambda_workspace && zip -r "$FINAL_ZIP_NAME" "$SELECTED_FILE")
    ZIP_FILE="$FINAL_ZIP_NAME"
    echo "Created zip file ./lambda_workspace/$FINAL_ZIP_NAME from $SELECTED_FILE."
    break
  else
    echo "Invalid option. Please select 1 or 2."
  fi
done

aws --endpoint-url=http://localhost:4566 lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file "fileb://$PWD/lambda_workspace/$ZIP_FILE" \
    --no-cli-pager