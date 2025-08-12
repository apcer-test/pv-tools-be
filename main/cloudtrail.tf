# CloudTrail Configuration
# Creates CloudTrail trail with S3 bucket for logs across all regions

# S3 Bucket for CloudTrail Logs
module "cloudtrail_s3_bucket" {
  count  = var.create_cloudtrail ? 1 : 0
  source = "../modules/s3"

  bucket_name        = "${var.project_name}-${var.env}-cloudtrail-logs"
  project_name       = var.project_name
  app_name           = var.project_name
  env                = var.env
  enable_encryption  = true
  enable_versioning  = true
  block_public_access = true
  enable_lifecycle   = true
  lifecycle_rules = [
    {
      id                         = "cloudtrail_logs_lifecycle"
      enabled                    = true
      filter_prefix              = ""
      expiration_days            = 60  # 2 months
      noncurrent_version_expiration_days = 60
      transition_to_ia_days      = 30
      transition_to_glacier_days = 0
    }
  ]
  tags = {
    Name        = "${var.project_name}-${var.env}-cloudtrail-logs"
    Project     = var.project_name
    Service     = "cloudtrail-logs-bucket"
    Environment = var.env
    Terraform   = "true"
  }
}

# S3 Bucket Policy for CloudTrail
resource "aws_s3_bucket_policy" "cloudtrail_logs" {
  count  = var.create_cloudtrail ? 1 : 0
  bucket = module.cloudtrail_s3_bucket[0].bucket_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = module.cloudtrail_s3_bucket[0].bucket_arn
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${module.cloudtrail_s3_bucket[0].bucket_arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })

  depends_on = [module.cloudtrail_s3_bucket]
}

# CloudWatch Log Group for CloudTrail
module "cloudwatch" {
  count  = var.create_cloudtrail ? 1 : 0
  source = "../modules/cloudwatch"

  log_group_name    = "/aws/cloudtrail/${var.project_name}-${var.env}"
  retention_in_days = 30
  project_name      = var.project_name
  env               = var.env
  tags = {
    Name        = "${var.project_name}-${var.env}-cloudtrail-logs"
    Project     = var.project_name
    Service     = "cloudtrail-log-group"
    Environment = var.env
    Terraform   = "true"
  }
}

# IAM Role for CloudTrail to CloudWatch
module "cloudtrail_cloudwatch_role" {
  count  = var.create_cloudtrail ? 1 : 0
  source = "../modules/iam/cloudtrail_cloudwatch_role"

  role_name               = "${var.project_name}-cloudtrail-cloudwatch-role${var.env}"
  policy_name             = "${var.project_name}-cloudtrail-cloudwatch-policy${var.env}"
  project_name            = var.project_name
  env                     = var.env
  tags                    = {}
  cloudwatch_log_group_arn = module.cloudwatch[0].log_group_arn
}

# CloudTrail Module
module "cloudtrail" {
  count  = var.create_cloudtrail ? 1 : 0
  source = "../modules/cloudtrail"

  create_cloudtrail             = true
  project_name                  = var.project_name
  env                           = var.env
  region                        = var.region
  cloudtrail_s3_bucket_name     = module.cloudtrail_s3_bucket[0].bucket_name
  cloudwatch_log_group_arn      = "${module.cloudwatch[0].log_group_arn}:*"
  cloudtrail_cloudwatch_role_arn = module.cloudtrail_cloudwatch_role[0].role_arn
  tags = {
    Name        = "${var.project_name}-${var.env}-cloudtrail"
    Project     = var.project_name
    Service     = "cloudtrail"
    Environment = var.env
    Terraform   = "true"
  }
} 