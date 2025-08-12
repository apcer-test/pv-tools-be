# Security Module - AWS Config, GuardDuty, and WAF

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0.0"
      configuration_aliases = [aws.us_east_1]
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

##########################################################
# AWS Config
##########################################################
# S3 Bucket for AWS Config
resource "aws_s3_bucket" "config" {
  count  = var.create_aws_config ? 1 : 0
  bucket = "${var.project_name}-${var.env}-config-logs"

  tags = {
    Name        = "${var.project_name}-${var.env}-config-logs"
    Project     = var.project_name
    Service     = "aws-config-logs"
    Environment = var.env
    Terraform   = "true"
  }
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "config" {
  count  = var.create_aws_config ? 1 : 0
  bucket = aws_s3_bucket.config[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "config" {
  count  = var.create_aws_config ? 1 : 0
  bucket = aws_s3_bucket.config[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "config" {
  count  = var.create_aws_config ? 1 : 0
  bucket = aws_s3_bucket.config[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Policy for AWS Config
resource "aws_s3_bucket_policy" "config" {
  count  = var.create_aws_config ? 1 : 0
  bucket = aws_s3_bucket.config[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSConfigBucketPermissionsCheck"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.config[0].arn
      },
      {
        Sid    = "AWSConfigBucketDelivery"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.config[0].arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.config]
}

# IAM Role for AWS Config
resource "aws_iam_role" "config" {
  count = var.create_aws_config ? 1 : 0
  name  = "${var.project_name}-config-role${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-config-role${var.env}"
    Project     = var.project_name
    Service     = "aws-config-role"
    Environment = var.env
    Terraform   = "true"
  }
}

# IAM Role Policy for AWS Config
resource "aws_iam_role_policy" "config" {
  count = var.create_aws_config ? 1 : 0
  name  = "${var.project_name}-config-policy${var.env}"
  role  = aws_iam_role.config[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.config[0].arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetBucketAcl"
        ]
        Resource = aws_s3_bucket.config[0].arn
      }
    ]
  })
}

# AWS Config Configuration Recorder
resource "aws_config_configuration_recorder" "main" {
  count = var.create_aws_config ? 1 : 0
  name  = "${var.project_name}-${var.env}-config-recorder"

  role_arn = aws_iam_role.config[0].arn

  recording_group {
    all_supported = true
  }

  depends_on = [aws_iam_role_policy.config]
}

# AWS Config Delivery Channel
resource "aws_config_delivery_channel" "main" {
  count = var.create_aws_config ? 1 : 0
  name  = "${var.project_name}-${var.env}-config-delivery"

  s3_bucket_name = aws_s3_bucket.config[0].id
  s3_key_prefix  = "config"

  depends_on = [aws_config_configuration_recorder.main]
}

# AWS Config Configuration Recorder Status
resource "aws_config_configuration_recorder_status" "main" {
  count = var.create_aws_config ? 1 : 0
  name  = aws_config_configuration_recorder.main[0].name
  is_enabled = true

  depends_on = [aws_config_delivery_channel.main]
}

##########################################################
# Amazon GuardDuty
##########################################################
# GuardDuty Detector
resource "aws_guardduty_detector" "main" {
  count = var.create_guardduty ? 1 : 0
  enable = true

  tags = {
    Name        = "${var.project_name}-${var.env}-guardduty"
    Project     = var.project_name
    Service     = "guardduty"
    Environment = var.env
    Terraform   = "true"
  }
}

# GuardDuty S3 Protection
resource "aws_guardduty_detector_feature" "s3_protection" {
  count = var.create_guardduty ? 1 : 0
  detector_id = aws_guardduty_detector.main[0].id
  name        = "S3_DATA_EVENTS"
  status      = "ENABLED"
}

# GuardDuty EKS Protection
resource "aws_guardduty_detector_feature" "eks_protection" {
  count = var.create_guardduty ? 1 : 0
  detector_id = aws_guardduty_detector.main[0].id
  name        = "EKS_AUDIT_LOGS"
  status      = "ENABLED"
}

# GuardDuty RDS Protection
resource "aws_guardduty_detector_feature" "rds_protection" {
  count = var.create_guardduty ? 1 : 0
  detector_id = aws_guardduty_detector.main[0].id
  name        = "RDS_LOGIN_EVENTS"
  status      = "ENABLED"
}

##########################################################
# AWS WAF
##########################################################
# WAF IP Set for Known IPs
resource "aws_wafv2_ip_set" "known_ips" {
  count = var.create_waf ? 1 : 0
  provider = aws.us_east_1
  name  = "${var.project_name}-${var.env}-known-ips"

  scope              = "CLOUDFRONT"
  ip_address_version = "IPV4"
  addresses          = var.known_ip_addresses

  tags = {
    Name        = "${var.project_name}-${var.env}-known-ips"
    Project     = var.project_name
    Service     = "waf-ip-set"
    Environment = var.env
    Terraform   = "true"
  }
}

# WAF Web ACL for Admin
resource "aws_wafv2_web_acl" "admin" {
  count = var.create_waf ? 1 : 0
  provider = aws.us_east_1
  name  = "${var.project_name}-${var.env}-admin-web-acl"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  # Allow OPTIONS rule
  rule {
    name     = "AllowOPTIONS"
    priority = 0

    action {
      allow {}
    }

    statement {
      byte_match_statement {
        search_string = "OPTIONS"

        field_to_match {
          method {}
        }

        positional_constraint = "EXACTLY"
        text_transformation {
          priority = 0
          type     = "NONE"
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AllowOPTIONS"
      sampled_requests_enabled   = true
    }
  }

  # Common Rules with scope-down
  rule {
    name     = "AWSCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # Allow Known IPs Rule
  rule {
    name     = "AllowKnownIPs"
    priority = 2

    action {
      allow {}
    }

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.known_ips[0].arn
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AllowKnownIPs"
      sampled_requests_enabled   = true
    }
  }

  # AI Bot Control Rule
  rule {
    name     = "AWSManagedBotControlRule"
    priority = 3
    override_action {
      none {}
    }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesBotControlRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "BotControlRule"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "AdminWebACLMetric"
    sampled_requests_enabled   = true
  }

  tags = {
    Name        = "${var.project_name}-${var.env}-admin-web-acl"
    Project     = var.project_name
    Service     = "waf-admin-web-acl"
    Environment = var.env
    Terraform   = "true"
  }
}

# WAF Web ACL for API
resource "aws_wafv2_web_acl" "api" {
  count = var.create_waf ? 1 : 0
  provider = aws.us_east_1
  name  = "${var.project_name}-${var.env}-api-web-acl"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  # Allow OPTIONS rule
  rule {
    name     = "AllowOPTIONS"
    priority = 0

    action {
      allow {}
    }

    statement {
      byte_match_statement {
        search_string = "OPTIONS"

        field_to_match {
          method {}
        }

        positional_constraint = "EXACTLY"
        text_transformation {
          priority = 0
          type     = "NONE"
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AllowOPTIONS"
      sampled_requests_enabled   = true
    }
  }

  # Common Rules with scope-down
  rule {
    name     = "AWSCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # SQLi Rule
  rule {
    name     = "AWSManagedSQLiRuleSet"
    priority = 2
    override_action {
      none {}
    }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "SQLiRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # Known Bad Inputs
  rule {
    name     = "AWSManagedKnownBadInputs"
    priority = 3
    override_action {
      none {}
    }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "KnownBadInputs"
      sampled_requests_enabled   = true
    }
  }

  # Rate-based rule
  rule {
    name     = "RateLimitRule"
    priority = 4  
    action {
      block {}
    }
    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  # AI Bot Control Rule
  rule {
    name     = "AWSManagedBotControlRule"
    priority = 5
    override_action {
      none {}
    }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesBotControlRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "BotControlRule"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "APIWebACLMetric"
    sampled_requests_enabled   = true
  }

  tags = {
    Name        = "${var.project_name}-${var.env}-api-web-acl"
    Project     = var.project_name
    Service     = "waf-api-web-acl"
    Environment = var.env
    Terraform   = "true"
  }
}

##########################################################
# AWS Inspector
##########################################################
resource "aws_inspector2_enabler" "main" {
  count = var.create_inspector ? 1 : 0
  
  account_ids    = [data.aws_caller_identity.current.account_id]
  resource_types = ["EC2", "ECR", "LAMBDA", "LAMBDA_CODE"]
}

##########################################################
# AWS Security Hub
##########################################################
resource "aws_securityhub_account" "main" {
  count = var.create_security_hub ? 1 : 0
  
  enable_default_standards = true
  auto_enable_controls    = true
}

# Security Hub Standards Subscription (CIS AWS Foundations Benchmark)
resource "aws_securityhub_standards_subscription" "cis" {
  count = var.create_security_hub ? 1 : 0
  
  standards_arn = "arn:aws:securityhub:${data.aws_region.current.name}::standards/cis-aws-foundations-benchmark/v/1.4.0"

  depends_on = [aws_securityhub_account.main]
}

# Security Hub Standards Subscription (AWS Foundational Security Best Practices)
resource "aws_securityhub_standards_subscription" "foundational" {
  count = var.create_security_hub ? 1 : 0
  
  standards_arn = "arn:aws:securityhub:${data.aws_region.current.name}::standards/aws-foundational-security-best-practices/v/1.0.0"

  depends_on = [aws_securityhub_account.main]
}

# Security Hub Finding Aggregator (if multi-account)
resource "aws_securityhub_finding_aggregator" "main" {
  count = var.create_security_hub && var.enable_finding_aggregator ? 1 : 0
  
  linking_mode = "ALL_REGIONS_EXCEPT_SPECIFIED"
  
  specified_regions = var.finding_aggregator_excluded_regions
}



 