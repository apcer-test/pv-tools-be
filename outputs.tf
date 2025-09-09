# CloudWatch Synthetics Module Outputs

output "synthetics_role_arn" {
  description = "ARN of the Synthetics execution role"
  value       = var.create_synthetics ? aws_iam_role.synthetics_role[0].arn : ""
}

output "synthetics_artifacts_bucket_name" {
  description = "Name of the S3 bucket for canary artifacts"
  value       = var.create_synthetics ? aws_s3_bucket.synthetics_artifacts[0].bucket : ""
}

output "synthetics_artifacts_bucket_arn" {
  description = "ARN of the S3 bucket for canary artifacts"
  value       = var.create_synthetics ? aws_s3_bucket.synthetics_artifacts[0].arn : ""
}

output "canary_names" {
  description = "Names of all created canaries"
  value = var.create_synthetics ? {
    for k, v in aws_synthetics_canary.canaries : k => v.name
  } : {}
}

output "canary_arns" {
  description = "ARNs of all created canaries"
  value = var.create_synthetics ? {
    for k, v in aws_synthetics_canary.canaries : k => v.arn
  } : {}
}

output "alarm_names" {
  description = "Names of all created alarms"
  value = var.create_synthetics ? {
    for k, v in aws_cloudwatch_metric_alarm.canary_alarms : k => v.alarm_name
  } : {}
} 