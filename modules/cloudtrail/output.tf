# CloudTrail Module Outputs

# CloudTrail outputs
output "cloudtrail_arn" {
  description = "ARN of the CloudTrail trail"
  value       = var.create_cloudtrail ? aws_cloudtrail.main[0].arn : null
}

output "cloudtrail_name" {
  description = "Name of the CloudTrail trail"
  value       = var.create_cloudtrail ? aws_cloudtrail.main[0].name : null
}

output "cloudtrail_home_region" {
  description = "Home region of the CloudTrail trail"
  value       = var.create_cloudtrail ? aws_cloudtrail.main[0].home_region : null
}

 