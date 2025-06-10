def lambda_handler(event, context):
    # This function will be triggered by events from API Gateway or other AWS services.
    # You can access the event data and context information here.
    
    # Example response
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }