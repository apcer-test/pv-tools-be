# Outputs for CloudTrail to CloudWatch IAM Role

output "role_arn" {
  description = "ARN of the IAM role"
  value       = aws_iam_role.cloudtrail_cloudwatch.arn
}

output "role_name" {
  description = "Name of the IAM role"
  value       = aws_iam_role.cloudtrail_cloudwatch.name
} 