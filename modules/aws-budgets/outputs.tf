# AWS Budgets Module Outputs

output "budget_id" {
  description = "ID of the created budget"
  value       = var.create_budget ? aws_budgets_budget.main[0].id : null
}

output "budget_arn" {
  description = "ARN of the created budget"
  value       = var.create_budget ? aws_budgets_budget.main[0].arn : null
}

output "budget_name" {
  description = "Name of the created budget"
  value       = var.create_budget ? aws_budgets_budget.main[0].name : null
}

output "budget_notifications" {
  description = "Budget notification configurations"
  value       = var.create_budget ? aws_budgets_budget.main[0].notification : null
}

output "cloudwatch_alarm_names" {
  description = "Names of the created CloudWatch alarms"
  value       = var.create_budget && var.create_budget_alarm ? [for alarm in aws_cloudwatch_metric_alarm.budget_alarm : alarm.alarm_name] : []
}

output "cloudwatch_alarm_arns" {
  description = "ARNs of the created CloudWatch alarms"
  value       = var.create_budget && var.create_budget_alarm ? [for alarm in aws_cloudwatch_metric_alarm.budget_alarm : alarm.arn] : []
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for budget notifications"
  value       = var.create_budget && var.create_sns_topic ? aws_sns_topic.budget_notifications[0].arn : null
}

output "sns_topic_name" {
  description = "Name of the SNS topic for budget notifications"
  value       = var.create_budget && var.create_sns_topic ? aws_sns_topic.budget_notifications[0].name : null
}

output "sns_subscription_arns" {
  description = "ARNs of the SNS topic subscriptions"
  value       = var.create_budget && var.create_sns_topic ? [for subscription in aws_sns_topic_subscription.budget_email : subscription.arn] : []
}

output "iam_policy_arn" {
  description = "ARN of the IAM policy for budget notifications"
  value       = var.create_budget && var.create_sns_topic ? aws_iam_policy.budget_notifications[0].arn : null
}

output "budget_configuration" {
  description = "Complete budget configuration"
  value = var.create_budget ? {
    budget_id     = aws_budgets_budget.main[0].id
    budget_arn    = aws_budgets_budget.main[0].arn
    budget_name   = aws_budgets_budget.main[0].name
    budget_type   = aws_budgets_budget.main[0].budget_type
    limit_amount  = aws_budgets_budget.main[0].limit_amount
    limit_unit    = aws_budgets_budget.main[0].limit_unit
    time_unit     = aws_budgets_budget.main[0].time_unit
    notifications = aws_budgets_budget.main[0].notification
  } : null
} 