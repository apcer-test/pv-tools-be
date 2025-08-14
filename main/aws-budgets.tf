# AWS Budgets Configuration
# Creates budget monitoring with threshold alerts and email notifications

module "aws_budgets" {
  count  = var.create_aws_budgets ? 1 : 0
  source = "../modules/aws-budgets"

  create_budget = true
  project_name  = var.project_name
  env           = var.env

  # Budget configuration
  budget_type        = var.aws_budgets.budget_type
  budget_limit_amount = var.aws_budgets.budget_limit_amount
  budget_limit_unit   = var.aws_budgets.budget_limit_unit
  budget_time_unit    = var.aws_budgets.budget_time_unit
  cost_filters        = var.aws_budgets.cost_filters

  # Budget notifications
  budget_notifications = var.aws_budgets.budget_notifications

  # CloudWatch alarm configuration
  create_budget_alarm      = var.aws_budgets.create_budget_alarm
  alarm_evaluation_periods = var.aws_budgets.alarm_evaluation_periods
  alarm_period            = var.aws_budgets.alarm_period

  # SNS configuration
  create_sns_topic         = var.aws_budgets.create_sns_topic
  subscriber_email_addresses = var.aws_budgets.subscriber_email_addresses

  # Additional configuration
  alarm_actions = []
  ok_actions    = []

  tags = {
    Name        = "${var.project_name}-${var.env}-budget"
    Project     = var.project_name
    Service     = "aws-budgets"
    Environment = var.env
    Terraform   = "true"
  }
} 