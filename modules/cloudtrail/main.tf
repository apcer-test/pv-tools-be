# CloudTrail Module - Creates CloudTrail trail with S3 bucket for logs

# Data source to get current AWS account and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}



##########################################################
# CloudTrail Trail
##########################################################
resource "aws_cloudtrail" "main" {
  count = var.create_cloudtrail ? 1 : 0

  name                          = "${var.project_name}-${var.env}-trail"
  s3_bucket_name                = var.cloudtrail_s3_bucket_name
  cloud_watch_logs_group_arn    = var.cloudwatch_log_group_arn
  cloud_watch_logs_role_arn     = var.cloudtrail_cloudwatch_role_arn
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true

  event_selector {
    read_write_type                 = "All"
    include_management_events       = true
    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3:::"]
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.env}-cloudtrail"
    Project     = var.project_name
    Service     = "cloudtrail"
    Environment = var.env
    Terraform   = "true"
  }
} 