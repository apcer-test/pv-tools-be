# SNS Module Outputs

output "topic_arn" {
  description = "ARN of the SNS topic"
  value       = var.create_topic ? aws_sns_topic.main[0].arn : null
}

output "topic_name" {
  description = "Name of the SNS topic"
  value       = var.create_topic ? aws_sns_topic.main[0].name : null
}

output "topic_id" {
  description = "ID of the SNS topic"
  value       = var.create_topic ? aws_sns_topic.main[0].id : null
}

output "subscription_arns" {
  description = "ARNs of the SNS topic subscriptions"
  value       = var.create_topic ? [for subscription in aws_sns_topic_subscription.main : subscription.arn] : []
}

output "platform_application_arns" {
  description = "ARNs of the SNS platform applications"
  value       = var.create_platform_applications ? [for app in aws_sns_platform_application.main : app.arn] : []
}

output "platform_endpoint_arns" {
  description = "ARNs of the SNS platform endpoints"
  value       = var.create_platform_endpoints ? [for endpoint in aws_sns_platform_endpoint.main : endpoint.arn] : []
} 