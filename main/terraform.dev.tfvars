# ===================================================
# APCER-PV-TOOL Development Environment Configuration
# ===================================================

# Environment Configuration
environment = "dev"
project_name = "apcer-pv-tool"
region = "eu-west-2"

# VPC Configuration
cidr = "10.10.0.0/16"
availability_zones = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]

# =============================
# CORE INFRASTRUCTURE SERVICES
# =============================

# VPC
create_vpc = true

# Application Load Balancer
create_alb = true
alb_internal = false
alb_enable_deletion_protection = true

# ===================
# COMPUTE SERVICES
# ===================

# ECS Fargate
create_ecs = true
ecs_cluster_name = "apcer-pv-tool-dev-cluster"
services = {
  service1 = {
    container_name      = "api"
    container_port      = 8000
    cpu                 = 480
    memory              = 768
    domain              = "api-dev.webelight.co.in"  # Updated domain for dev environment
    command             = ["/bin/sh", "-c", "python main.py migrate && python main.py run"]
    health_check_path   = "/healthcheck"
    repository_path     = "APCER-Life-Sciences-Inc/pv-tool-be"  # GitHub repository path
    repository_branch   = "main"
    env_bucket_path     = "api/dev"
    compute_type        = "BUILD_GENERAL1_SMALL"
    create_cloudfront   = true
    enable_xray         = true
    xray_daemon_cpu    = 32
    xray_daemon_memory = 256
  }
}
# EC2 Bastion Host
create_ec2_bastion = true
bastion_instance_type = "t3.micro"
bastion_key_name = "apcer-pv-tool-dev-bastion"

# =================
# STORAGE SERVICES
# =================

# S3 Buckets
create_s3 = true
s3_buckets = {
  frontend = {
    name = "apcer-pv-tool-frontend-dev"
    versioning = true
    encryption = true
    public_access_block = true
    cors_configuration = true
    cors_rules = [
      {
        allowed_headers = ["*"]
        allowed_methods = ["GET", "HEAD", "OPTIONS"]
        allowed_origins = ["*"]
        expose_headers = ["ETag", "Content-Length"]
        max_age_seconds = 3600
      }
    ]
    lifecycle_rules = {
      delete_after_days = 90
    }
    enable_oac = true
    create = true
    create_codepipeline = true
    repository_path = "frontend"
  }
}

# Frontend Configuration (for CodePipeline)
frontends = {
  frontend = {
    service_name         = "frontend"
    domain              = "frontend-dev.webelight.co.in"  # Update with your domain
    repository_path     = "APCER-Life-Sciences-Inc/pv-tool-fe"  # GitHub repository path
    repository_branch   = "main"
    bucket_path         = "frontend/dev"
    node_version        = "20.9.0"
    build_commands      = [
      "npm install",
      "npm run build"
    ]
    install_commands    = []
    compute_type        = "BUILD_GENERAL1_SMALL"
    create_codepipeline = true
    create             = true
    enable_oac         = true
    create_cloudfront  = true
  }
}

# ECR (Container Registry)
create_ecr = true
ecr_repositories = ["apcer-api-dev"]

# =============================================================================
# DATABASE SERVICES
# =============================================================================

# RDS PostgreSQL
create_rds = true
rds_instance_class = "db.t3.medium"
rds_allocated_storage = 20
rds_max_allocated_storage = 100
rds_multi_az = false
rds_backup_retention_period = 7
rds_backup_window = "03:00-04:00"
rds_maintenance_window = "sun:04:00-sun:05:00"
rds_deletion_protection = true
rds_skip_final_snapshot = true
rds_engine_version = "17.4"
rds_database_name = "apcer_pv_tool_dev"
rds_username = "apcer_admin"
# Password will be managed by AWS Secrets Manager
rds_manage_master_user_secret = true
rds_master_user_secret_kms_key_id = null  # Leave null to use default AWS managed key

# ElastiCache Redis (Disabled for now - confirm with backend dev)
create_elasticache = false

# =============================================================================
# CONTENT DELIVERY
# =============================================================================

# CloudFront
create_cloudfront = true
cloudfront_price_class = "PriceClass_100"
# IMPORTANT: Replace with your actual ACM certificate ARN from us-east-1 region
# The certificate must be valid and cover your domain names (e.g., *.apcer-pv-tool.com)
# You can create one in AWS Console or use AWS CLI: aws acm list-certificates --region us-east-1
cloudfront_acm_certificate_arn = "arn:aws:acm:us-east-1:912106457730:certificate/8b8ae7bb-b1ee-42a3-bd10-b6c72c7936e1"  # Example: "arn:aws:acm:us-east-1:123456789012:certificate/your-actual-cert-id"

# =============================================================================
# CI/CD SERVICES
# =============================================================================

# CodePipeline
create_codepipelines = true
version_control_type = "github"
# GitHub Personal Access Token for CodePipeline connections
# Create one at: https://github.com/settings/tokens
# Required scopes: repo, admin:repo_hook
github_token = "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"  # Add your GitHub Personal Access Token here

# CodeBuild
create_codebuild = true

# =============================================================================
# DISABLED SERVICES
# =============================================================================

# AWS Backup (Disabled for dev)
create_aws_backup = false

# WAF (Disabled)
create_waf = false

# GuardDuty (Disabled)
create_guardduty = false

# AWS Config (Disabled)
create_aws_config = false

# AWS Inspector (Disabled)
create_inspector = false

# AWS Security Hub (Disabled)
create_security_hub = false

# CloudWatch Synthetics (Disabled)
create_synthetics = false

# AWS X-Ray (Disabled)
create_xray = false

# AWS Budgets (Enabled for dev)
create_aws_budgets = true

# AWS Budgets Configuration
aws_budgets = {
  budget_type = "COST"
  budget_limit_amount = "200"
  budget_limit_unit = "USD"
  budget_time_unit = "MONTHLY"
  cost_filters = {}
  budget_notifications = [
    {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 80
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = ["dev-team@your-company.com"]  # Update with actual email
      subscriber_sns_topic_arns  = []
    },
    {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 100
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = ["dev-team@your-company.com"]  # Update with actual email
      subscriber_sns_topic_arns  = []
    }
  ]
  create_budget_alarm = true
  alarm_evaluation_periods = 1
  alarm_period = 86400
  create_sns_topic = true
  subscriber_email_addresses = ["dev-team@your-company.com"]  # Update with actual email
}

# Cognito (Disabled)
create_cognito = false

# CloudTrail (Disabled)
create_cloudtrail = false

# =============================================================================
# TAGS
# =============================================================================

tags = {
  Environment = "dev"
  Project     = "apcer-pv-tool"
  Owner       = "dev-team"
  CostCenter  = "development"
  ManagedBy   = "terraform"
} 