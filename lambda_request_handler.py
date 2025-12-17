import boto3
import json
import uuid
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('iam-access-sessions')

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Store request in DynamoDB
        table.put_item(Item={
            'request_id': request_id,
            'user_email': body.get('email', ''),
            'scope': body.get('scope', 'read'),
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        })
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'request_id': request_id,
                'message': 'Access request submitted successfully'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
