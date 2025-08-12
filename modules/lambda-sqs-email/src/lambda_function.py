import json
import logging

def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    for record in event.get('Records', []):
        try:
            body = record['body']
            logger.info(f"Processing SQS email job: {body}")
            # Here you would add your email processing logic
        except Exception as e:
            logger.error(f"Error processing record: {e}")

    return {
        'statusCode': 200,
        'body': json.dumps('Processed SQS email jobs')
    } 