import boto3
import json
import os
from datetime import datetime, timedelta

sts = boto3.client('sts')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('iam-access-sessions')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        request_id = event['request_id']
        user_email = event['user_email']
        
        # Get AWS account ID
        account_id = context.invoked_function_arn.split(':')[4]
        
        # Calculate expiration (24 hours)
        expiration = datetime.utcnow() + timedelta(hours=24)
        
        # Assume temporary role with STS
        response = sts.assume_role(
            RoleArn=f'arn:aws:iam::{account_id}:role/TempAccessRole',
            RoleSessionName=f'session-{request_id}',
            DurationSeconds=86400,  # 24 hours
            Tags=[
                {'Key': 'ExpiresAt', 'Value': expiration.isoformat()},
                {'Key': 'RequestId', 'Value': request_id},
                {'Key': 'UserEmail', 'Value': user_email}
            ]
        )
        
        credentials = response['Credentials']
        
        # Update DynamoDB with active session
        table.update_item(
            Key={'request_id': request_id},
            UpdateExpression='SET #st = :status, credentials = :creds, '
                           'expiration_time = :exp, ttl = :ttl',
            ExpressionAttributeNames={'#st': 'status'},
            ExpressionAttributeValues={
                ':status': 'active',
                ':creds': {
                    'AccessKeyId': credentials['AccessKeyId'],
                    'SecretAccessKey': credentials['SecretAccessKey'],
                    'SessionToken': credentials['SessionToken'],
                    'Expiration': credentials['Expiration'].isoformat()
                },
                ':exp': expiration.isoformat(),
                ':ttl': int(expiration.timestamp())
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Credentials provisioned successfully',
                'request_id': request_id
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
