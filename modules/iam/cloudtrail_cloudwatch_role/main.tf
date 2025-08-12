# IAM Role for CloudTrail to CloudWatch

resource "aws_iam_role" "cloudtrail_cloudwatch" {
  name = var.role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
      }
    ]
  })

  tags = merge({
    Name        = var.role_name
    Project     = var.project_name
    Service     = "cloudtrail-cloudwatch-role"
    Environment = var.env
    Terraform   = "true"
  }, var.tags)
}

resource "aws_iam_role_policy" "cloudtrail_cloudwatch" {
  name = var.policy_name
  role = aws_iam_role.cloudtrail_cloudwatch.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = "${var.cloudwatch_log_group_arn}:*"
      }
    ]
  })
} 