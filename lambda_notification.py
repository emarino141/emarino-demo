import boto3
import json
import urllib.parse
import os

sns = boto3.client('sns')

# Replace with your SNS topic ARN
SNS_TOPIC_ARN = 'arn:aws:sns:REGION:ACCOUNT:iam-notifications'

def lambda_handler(event, context):
    try:
        credentials = event['credentials']
        user_email = event['user_email']
        request_id = event['request_id']
        
        # Generate console federation URL
        console_url = generate_federation_url(
            credentials['AccessKeyId'],
            credentials['SecretAccessKey'],
            credentials['SessionToken']
        )
        
        # Create email message
        message = f'''Your AWS Temporary Access Credentials

================================================
ACCESS DETAILS
================================================

Access Key ID: {credentials['AccessKeyId']}

Secret Access Key: {credentials['SecretAccessKey']}

Session Token: {credentials['SessionToken']}

Expiration: {credentials['Expiration']}

================================================
AWS CONSOLE ACCESS
================================================

{console_url}

================================================
CLI CONFIGURATION
================================================

Export these in your terminal:

export AWS_ACCESS_KEY_ID="{credentials['AccessKeyId']}"
export AWS_SECRET_ACCESS_KEY="{credentials['SecretAccessKey']}"
export AWS_SESSION_TOKEN="{credentials['SessionToken']}"

================================================
SECURITY REMINDER
================================================

- These credentials expire in 24 hours
- Do not share these credentials
- Request ID: {request_id}

'''
        
        # Send via SNS
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f'AWS Temporary Access Credentials - {request_id}',
            Message=message,
            MessageAttributes={
                'email': {
                    'DataType': 'String',
                    'StringValue': user_email
                }
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Credentials sent successfully',
                'request_id': request_id
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def generate_federation_url(access_key, secret_key, session_token):
    """Generate AWS Console federation sign-in URL"""
    
    # Create session credentials JSON
    session_json = json.dumps({
        'sessionId': access_key,
        'sessionKey': secret_key,
        'sessionToken': session_token
    })
    
    # Get signin token
    request_parameters = f'?Action=getSigninToken&SessionDuration=43200&Session={urllib.parse.quote_plus(session_json)}'
    request_url = 'https://signin.aws.amazon.com/federation' + request_parameters
    
    # Note: In production, you would make an HTTP request here to get the signin token
    # For this example, we're returning the federation URL structure
    
    signin_token = 'SIGNIN_TOKEN_PLACEHOLDER'
    
    # Create federated console URL
    federation_url = (
        'https://signin.aws.amazon.com/federation'
        f'?Action=login&Issuer=TemporaryAccess&Destination={urllib.parse.quote_plus("https://console.aws.amazon.com/")}'
        f'&SigninToken={signin_token}'
    )
    
    return federation_url
