# AWS Budgets Module
# Creates budget monitoring with threshold alerts and email notifications

# AWS Budget
resource "aws_budgets_budget" "main" {
  count = var.create_budget ? 1 : 0
  
  name              = "${var.project_name}-${var.env}-budget"
  budget_type       = var.budget_type
  limit_amount      = var.budget_limit_amount
  limit_unit        = var.budget_limit_unit
  time_period_start = var.budget_time_period_start
  time_period_end   = var.budget_time_period_end
  time_unit         = var.budget_time_unit

  # Cost filters to scope the budget
  dynamic "cost_filters" {
    for_each = var.cost_filters
    content {
      name   = cost_filters.key
      values = cost_filters.value
    }
  }

  # Budget notifications
  dynamic "notification" {
    for_each = var.budget_notifications
    content {
      comparison_operator        = notification.value.comparison_operator
      threshold                  = notification.value.threshold
      threshold_type             = notification.value.threshold_type
      notification_type          = notification.value.notification_type
      subscriber_email_addresses = notification.value.subscriber_email_addresses
      subscriber_sns_topic_arns  = try(notification.value.subscriber_sns_topic_arns, [])
    }
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.env}-budget"
    Project     = var.project_name
    Service     = "aws-budgets"
    Environment = var.env
    Terraform   = "true"
  })
}

# CloudWatch Alarm for Budget Threshold
resource "aws_cloudwatch_metric_alarm" "budget_alarm" {
  for_each = var.create_budget && var.create_budget_alarm ? {
    for notification in var.budget_notifications : "${notification.threshold}${notification.threshold_type}" => notification
    if notification.notification_type == "ACTUAL" || notification.notification_type == "FORECASTED"
  } : {}

  alarm_name          = "${var.project_name}-${var.env}-budget-${each.value.threshold}${each.value.threshold_type}-alarm"
  comparison_operator = each.value.comparison_operator
  evaluation_periods  = var.alarm_evaluation_periods
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = var.alarm_period
  statistic           = "Maximum"
  threshold           = each.value.threshold
  alarm_description   = "Budget threshold alarm for ${var.project_name}-${var.env} at ${each.value.threshold}${each.value.threshold_type}"
  alarm_actions       = var.alarm_actions
  ok_actions          = var.ok_actions

  dimensions = {
    Currency = "USD"
    ServiceName = "Amazon Web Services"
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.env}-budget-alarm"
    Project     = var.project_name
    Service     = "cloudwatch-alarm"
    Environment = var.env
    Terraform   = "true"
  })
}

# SNS Topic for Budget Notifications (if not provided)
resource "aws_sns_topic" "budget_notifications" {
  count = var.create_budget && var.create_sns_topic ? 1 : 0
  
  name = "${var.project_name}-${var.env}-budget-notifications"
  
  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.env}-budget-sns"
    Project     = var.project_name
    Service     = "sns"
    Environment = var.env
    Terraform   = "true"
  })
}

# SNS Topic Subscription for Email Notifications
resource "aws_sns_topic_subscription" "budget_email" {
  for_each = var.create_budget && var.create_sns_topic ? toset(var.subscriber_email_addresses) : []
  
  topic_arn = aws_sns_topic.budget_notifications[0].arn
  protocol  = "email"
  endpoint  = each.value
}

# IAM Policy for Budget Notifications (if using SNS)
resource "aws_iam_policy" "budget_notifications" {
  count = var.create_budget && var.create_sns_topic ? 1 : 0
  
  name        = "${var.project_name}-${var.env}-budget-notifications-policy"
  description = "Policy for AWS Budget notifications"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.budget_notifications[0].arn
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.env}-budget-notifications-policy"
    Project     = var.project_name
    Service     = "iam-policy"
    Environment = var.env
    Terraform   = "true"
  })
} 