 resource "aws_sns_topic" "synthetics_alarms" {
   count  = var.create_synthetics ? 1 : 0
  name  = "${var.project_name}-${var.env}-synthetics-alarms"
}
resource "aws_sns_topic_subscription" "synthetics_emails" {
  count     = var.create_synthetics ? length(var.synthetics_alarm_emails) : 0
  topic_arn = aws_sns_topic.synthetics_alarms[0].arn
  protocol  = "email"
  endpoint  = var.synthetics_alarm_emails[count.index]
}

locals {
  synthetics_artifacts_bucket_name = "apcer-pv-tool-dev-synthetics-artifacts"
}

data "aws_iam_role" "synthetics_role" {
  name = "${var.project_name}-${var.env}-synthetics-role"
  # For you this resolves to: apcer-pv-tool-dev-synthetics-role
}
resource "aws_iam_policy" "synthetics_artifacts_s3" {
  name        = "${var.project_name}-${var.env}-synthetics-artifacts-s3"
  description = "Allow Synthetics canaries to write artifacts to S3"
  policy      = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:GetBucketLocation",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads"
        ],
        Resource = "arn:aws:s3:::${local.synthetics_artifacts_bucket_name}"
      },
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:AbortMultipartUpload",
          "s3:GetObject",
          "s3:ListMultipartUploadParts"
        ],
        Resource = "arn:aws:s3:::${local.synthetics_artifacts_bucket_name}/*"
      },
      {
        # The SDK tries to list all buckets to determine ownership; allow it.
        Effect = "Allow",
        Action = "s3:ListAllMyBuckets",
        Resource = "*"
      }
    ]
  })
}
# CloudWatch Synthetics Configuration
# Creates synthetic monitoring canaries for endpoint health checks

# CloudWatch Synthetics Module
module "synthetics" {
  count  = var.create_synthetics ? 1 : 0
  source = "../modules/cloudwatch-synthetics"

  create_synthetics = true
  project_name      = var.project_name
  env               = var.env
  artifacts_bucket_arn = ""  # Will be auto-created by the module
  synthetics_alarm_emails = var.synthetics_alarm_emails

  # Canary configurations for monitoring endpoints
  canaries = {
    api_health_check = {
      name                = "${var.project_name}-${var.env}-api-health"
      runtime_version     = "syn-nodejs-puppeteer-6.2"
      start_canary        = true
      schedule_expression = var.synthetics.api_health_check.schedule
      timeout_in_seconds  = var.synthetics.api_health_check.timeout
      memory_in_mb        = var.synthetics.api_health_check.memory_size
      active_tracing      = true
      subnet_ids          = []
      security_group_ids  = []
      target_url          = var.synthetics.api_health_check.target_url
    }
    admin_health_check = {
      name                = "${var.project_name}-${var.env}-admin-health"
      runtime_version     = "syn-nodejs-puppeteer-6.2"
      start_canary        = true
      schedule_expression = var.synthetics.admin_health_check.schedule
      timeout_in_seconds  = var.synthetics.admin_health_check.timeout
      memory_in_mb        = var.synthetics.admin_health_check.memory_size
      active_tracing      = true
      subnet_ids          = []
      security_group_ids  = []
      target_url          = var.synthetics.admin_health_check.target_url
    }
  }

  # Alarm actions (SNS topics, etc.)
  
  alarm_actions = length(var.synthetics_alarm_emails) > 0 ? [aws_sns_topic.synthetics_alarms[0].arn] : []

  tags = {
    Name        = "${var.project_name}-${var.env}-synthetics"
    Project     = var.project_name
    Service     = "synthetics"
    Environment = var.env
    Terraform   = "true"
  }
} 