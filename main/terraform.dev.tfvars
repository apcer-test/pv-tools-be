# ===================================================
# APCER-PV-TOOL Development Environment Configuration
# ===================================================

# Environment Configuration
environment = "dev"
project_name = "apcer-pv-tool"
region = "eu-west-2"

# VPC Configuration
cidr = "10.10.0.0/16"
vpc_availability_zones = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]

# VPC
create_vpc = true

# Application Load Balancer
create_alb = true
alb_internal = false
alb_enable_deletion_protection = true


# ECS Fargate
create_ecs = true
ecs_cluster_name = "apcer-pv-tool-dev-cluster"
services = {
  service1 = {
    container_name      = "api"
    container_port      = 9094
    cpu                 = 1024
    memory              = 2048
    domain              = "api-dev.apcerls.com"  # Updated domain for dev environment
    command             = ["/bin/sh", "-c", "python main.py migrate && python main.py run"]
    health_check_path   = "/healthcheck"
    repository_path     = "APCER-Life-Sciences-Inc/pv-tool-be"  # GitHub repository path
    repository_branch   = "main"
    env_bucket_path     = "api/dev"
    compute_type        = "BUILD_GENERAL1_SMALL"
    create_cloudfront   = true
    enable_xray         = true
    xray_daemon_cpu    = 0
    xray_daemon_memory = 512
    use_custom_buildspec = true
    enable_exec         = true
    # Celery worker container configuration
    enable_celery_worker = true
    celery_worker_command = ["python", "-m", "celery", "--app=core.utils.celery_worker", "worker", "--queues=main-queue", "--concurrency=5", "-E"]
    celery_worker_cpu    = 1024
    celery_worker_memory = 1024
  }
}
# EC2 Bastion Host
create_ec2_bastion = true
bastion_instance_type = "t3.micro"
bastion_key_name = "apcer-pv-tool-dev-bastion"


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

# Storage buckets for environment files and CodePipeline artifacts
storage_buckets = {
  env_bucket = {
    service_name        = "env"
    enable_versioning   = true
    service_folders     = ["frontend", "api"]
    lifecycle_rules     = []
  }
  codepipeline_artifacts_bucket = {
    service_name        = "codepipeline-artifacts"
    lifecycle_rules     = []
  }
}

# Frontend Configuration (for CodePipeline)
frontends = {
  frontend = {
    service_name         = "frontend"
    domain              = "fe-dev.apcerls.com"  # Primary domain
    cloudfront_aliases   = ["fe-dev.apcerls.com"]  # Primary and alternate domain
    repository_path     = "APCER-Life-Sciences-Inc/pv-tool-fe"  # GitHub repository path
    repository_branch   = "main"
    bucket_path         = "frontend/dev"
    node_version        = "22.11.0"
    build_commands      = []
    install_commands    = []
    compute_type        = "BUILD_GENERAL1_SMALL"
    create_codepipeline = true
    create             = true
    enable_oac         = true
    create_cloudfront  = true
    use_custom_buildspec = true
  }
}

# ECR (Container Registry)
create_ecr = true
ecr_repositories = ["apcer-api-dev"]

# RDS PostgreSQL
create_rds = true
rds_engine = "postgres"
rds_engine_version = "17.4"
rds_instance_class = "db.t3.medium"
rds_allocated_storage = 20
rds_max_allocated_storage = 100
rds_multi_az = false
rds_backup_retention_period = 7
rds_backup_window = "03:00-04:00"
rds_maintenance_window = "sun:04:00-sun:05:00"
rds_deletion_protection = true
rds_skip_final_snapshot = true
rds_database_name = "apcer_pv_tool_dev"
rds_username = "apcer_admin"
# Password will be managed by AWS Secrets Manager
rds_manage_master_user_secret = true
rds_master_user_secret_kms_key_id = null  # Leave null to use default AWS managed key

# ElastiCache Redis
create_elasticache = true
elasticache_engine = "redis"
elasticache_node_type = "cache.t3.micro"
elasticache_num_cache_nodes = 1
elasticache_parameter_group_name = "default.redis7"
elasticache_port = 6379
elasticache_subnet_group_name = "apcer-pv-tool-dev-elasticache-subnet-group"
elasticache_security_group_ids = ["apcer-pv-tool-dev-elasticache-sg"]
elasticache_engine_version = "7.0"
elasticache_automatic_failover_enabled = false
elasticache_multi_az_enabled = false
elasticache_at_rest_encryption_enabled = true
elasticache_transit_encryption_enabled = true
elasticache_auth_token = null  # Set to a secure token if needed
elasticache_maintenance_window = "sun:05:00-sun:06:00"
elasticache_snapshot_window = "04:00-05:00"
elasticache_snapshot_retention_limit = 7

# =============================================================================
# CONTENT DELIVERY
# =============================================================================

# CloudFront
create_cloudfront = true
cloudfront_price_class = "PriceClass_100"
# ACM Certificate Configuration
# Leave empty to automatically create certificate for your domain
cloudfront_acm_certificate_arn = ""  # Will auto-create certificate for *.webelight.co.in

# ACM Certificate Creation
create_acm_certificate = true
acm_domain_name = "*.apcerls.com"
acm_subject_alternative_names = ["apcerls.com"]
acm_validation_method = "DNS"
route53_zone_id = ""  # Not using Route53; will output CNAMEs for manual DNS

# =============================================================================
# CI/CD SERVICES
# =============================================================================

# CodePipeline
create_codepipelines = true
version_control_type = "github"
# CodeBuild
create_codebuild = true

# ===================
# DISABLED SERVICES
# ===================

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
  budget_limit_amount = "100"
  budget_limit_unit = "USD"
  budget_time_unit = "MONTHLY"
  cost_filters = {}
  budget_notifications = [
    {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 80
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = ["vinit.shah@apcerls.com", "amit.chaubey@apcerls.com"]
      subscriber_sns_topic_arns  = []
    },
    {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 100
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = ["vinit.shah@apcerls.com", "amit.chaubey@apcerls.com"]
      subscriber_sns_topic_arns  = []
    }
  ]
  create_budget_alarm = true
  alarm_evaluation_periods = 1
  alarm_period = 86400
  create_sns_topic = true
  subscriber_email_addresses = ["vinit.shah@apcerls.com", "amit.chaubey@apcerls.com"]
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