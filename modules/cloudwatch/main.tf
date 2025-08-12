# CloudWatch Log Group Module for CloudTrail

resource "aws_cloudwatch_log_group" "cloudtrail" {
  name              = var.log_group_name
  retention_in_days = var.retention_in_days

  tags = merge({
    Name        = var.log_group_name
    Project     = var.project_name
    Service     = "cloudtrail-log-group"
    Environment = var.env
    Terraform   = "true"
  }, var.tags)
} 