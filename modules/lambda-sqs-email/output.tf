output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.sqs_email_processor.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.sqs_email_processor.function_name
} 