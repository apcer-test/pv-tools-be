# Security Module Outputs

# AWS Config Outputs
output "config_recorder_name" {
  description = "Name of the AWS Config recorder"
  value       = var.create_aws_config ? aws_config_configuration_recorder.main[0].name : null
}

output "config_delivery_channel_name" {
  description = "Name of the AWS Config delivery channel"
  value       = var.create_aws_config ? aws_config_delivery_channel.main[0].name : null
}

output "config_s3_bucket_name" {
  description = "Name of the S3 bucket for AWS Config logs"
  value       = var.create_aws_config ? aws_s3_bucket.config[0].id : null
}

output "config_s3_bucket_arn" {
  description = "ARN of the S3 bucket for AWS Config logs"
  value       = var.create_aws_config ? aws_s3_bucket.config[0].arn : null
}

output "config_role_arn" {
  description = "ARN of the IAM role for AWS Config"
  value       = var.create_aws_config ? aws_iam_role.config[0].arn : null
}

# GuardDuty Outputs
output "guardduty_detector_id" {
  description = "ID of the GuardDuty detector"
  value       = var.create_guardduty ? aws_guardduty_detector.main[0].id : null
}

output "guardduty_detector_arn" {
  description = "ARN of the GuardDuty detector"
  value       = var.create_guardduty ? aws_guardduty_detector.main[0].arn : null
}

# WAF Outputs
output "waf_admin_web_acl_id" {
  description = "ID of the WAF Web ACL for Admin"
  value       = var.create_waf ? aws_wafv2_web_acl.admin[0].id : null
}

output "waf_admin_web_acl_arn" {
  description = "ARN of the WAF Web ACL for Admin"
  value       = var.create_waf ? aws_wafv2_web_acl.admin[0].arn : null
}

output "waf_api_web_acl_id" {
  description = "ID of the WAF Web ACL for API"
  value       = var.create_waf ? aws_wafv2_web_acl.api[0].id : null
}

output "waf_api_web_acl_arn" {
  description = "ARN of the WAF Web ACL for API"
  value       = var.create_waf ? aws_wafv2_web_acl.api[0].arn : null
}

# AWS Inspector Outputs
output "inspector_enabled" {
  description = "Whether AWS Inspector v2 is enabled"
  value       = var.create_inspector ? true : false
}

# AWS Security Hub Outputs
output "security_hub_account_id" {
  description = "ID of the Security Hub account"
  value       = var.create_security_hub ? aws_securityhub_account.main[0].id : null
} 