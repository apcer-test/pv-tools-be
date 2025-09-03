# ===================================================
# APCER-PV-TOOL Development Environment Configuration
# ===================================================

# Environment Configuration
env = "dev"
project_name = "apcer-pv-tool"
region = "eu-west-2"
app_name = "apcer-app"


# VPC Configuration
cidr = "10.10.0.0/16"
vpc_availability_zones = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]
create_database_subnet_group = true

# VPC
create_vpc = true

# Application Load Balancer
create_alb = true
alb_internal = false
alb_enable_deletion_protection = true


# ECS Fargate
create_ecs_ecosystem = true
ecs_cluster_name = "apcer-pv-tool-dev-cluster"
services = {
  service1 = {
    container_name      = "api"
    # Deploy celery service in the same pipeline using the same image
    ecs_additional_service_names = ["apcer-pv-tool-celery-dev"]
    container_port      = 9094
    cpu                 = 992
    memory              = 1792
    domain              = "api-dev.apcerls.com"  # Updated domain for dev environment
    command             = ["/bin/sh", "-c", "python main.py migrate && python main.py run"]
    health_check_path   = "/healthcheck"
    repository_path     = "APCER-Life-Sciences-Inc/pv-tool-be"
    repository_branch   = "main"
    env_bucket_path     = "api/dev"
    compute_type        = "BUILD_GENERAL1_SMALL"
    create_cloudfront   = true
    enable_xray         = true
    xray_daemon_cpu    = 32
    xray_daemon_memory = 256
    use_custom_buildspec = true
    enable_exec         = true
    # Celery worker configuration - disabled for API service
    enable_celery_worker = false
    # Service configuration
    desired_count       = 1
    # Auto-scaling configuration for API
    enable_auto_scaling = true
    min_capacity        = 1
    max_capacity        = 3
    target_cpu_utilization = 70
    target_memory_utilization = 80
  }
  # Celery worker as a separate ECS service (same image as API via container_name = "api")
  service2 = {
    container_name        = "api"                # reuse API ECR image
    service_resource_name = "celery"            # distinct ECS service/task/log group name
    container_port        = 9094
    cpu                   = 512
    memory                = 1024
    domain                = ""
    expose_via_alb        = false
    # Run celery worker instead of API entrypoint
    command               = ["python", "-m", "celery", "--app=core.utils.celery_worker", "worker", "--queues=main-queue", "--concurrency=5", "-E"]
    # Override health check to a simple process check
    health_check_path     = "/healthcheck"
    custom_healthcheck_command = ["CMD-SHELL", "curl -f https://api-dev.apcerls.com/health/worker/public || exit 1"]
    # Do not create a separate pipeline for celery
    repository_path       = ""
    repository_branch     = "main"
    env_bucket_path       = "api/dev"
    compute_type          = "BUILD_GENERAL1_SMALL"
    create_cloudfront     = false
    enable_xray           = false
    use_custom_buildspec  = true
    enable_exec           = true
    desired_count         = 1
    enable_auto_scaling   = true
    min_capacity          = 1
    max_capacity          = 5
    target_cpu_utilization = 70
    target_memory_utilization = 80
  }
}
# EC2 Bastion Host
create_bastion = true
bastion_instance_type = "t3.micro"
bastion_key_name = "apcer-pv-tool-dev-bastion"


# S3 Buckets
create_s3_buckets = true
s3_index_document = "index.html"
s3_error_document = "error.html"
s3_acl = "private"
s3_cors_rules = [
  {
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
  }
]
s3_lifecycle_rules = [
  {
    id = "cleanup-old-versions"
    enabled = true
    noncurrent_version_expiration_days = 30
  }
]
s3_folder_paths = ["logs", "temp", "uploads",]
s3_microservices = ["user-service", "notification-service", "workflow-service"]
s3_service_folders = ["frontend", "api", "media"]
s3_tags = {
  Environment = "dev"
  Project     = "apcer"
  Service     = "storage"
}


# Storage buckets for environment files and CodePipeline artifacts
storage_buckets = {
  env_bucket = {
    service_name        = "env"
    enable_versioning   = true
    service_folders     = ["frontend", "api", "microservices/document-microservice"]
    lifecycle_rules     = []
  }
  codepipeline_artifacts_bucket = {
    service_name        = "codepipeline-artifacts"
    lifecycle_rules     = []
  }
  document_microservice_bucket = {
    service_name        = "document-microservice"
    enable_versioning   = false
    service_folders     = ["uploads", "processed", "temp", "backups"]
    lifecycle_rules     = [
      {
        id = "cleanup-temp-files"
        enabled = true
        expiration_days = 7
        prefix = "temp/"
      },
      {
        id = "archive-old-backups"
        enabled = true
        noncurrent_version_expiration_days = 90
        prefix = "backups/"
      }
    ]
  }
  media_bucket = {
    service_name        = "media"
    enable_versioning   = true
    cloudfront_aliases   = ["media-dev.apcerls.com"]
    cors_rules = [
      {
        allowed_methods  = ["POST", "GET", "PUT"]
        allowed_origins  = [
          "https://fe-dev.apcerls.com",
          "http://localhost:4200",
          "http://localhost:5173",
          "http://localhost:3000"
        ]
        allowed_headers  = ["*"]
        expose_headers   = ["ETag", "x-amz-server-side-encryption", "x-amz-request-id", "x-amz-id-2"]
        max_age_seconds  = 3000
      }
    ]
    service_folders     = []
    lifecycle_rules     = [
      {
        id = "cleanup-old-versions"
        enabled = true
        noncurrent_version_expiration_days = 30
      }
    ]
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
    # Enable static website hosting
    enable_website = false
    index_document = "index.html"
    error_document = "error.html"
    # Error pages configuration for CloudFront
    error_pages = [
      {
        error_code = 403
        response_code = "200"
        response_page_path = "/index.html"
        error_caching_min_ttl = 0
      },
      {
        error_code = 404
        response_code = "200"
        response_page_path = "/index.html"
        error_caching_min_ttl = 0
      }
    ]
  }
  media = {
    service_name         = "media"
    domain              = "media-dev.apcerls.com"  # Primary domain
    cloudfront_aliases   = ["media-dev.apcerls.com"]  # Primary and alternate domain
    repository_path     = ""  # No repository needed for static media
    repository_branch   = "main"
    bucket_path         = "media/dev"
    node_version        = "22.11.0"
    build_commands      = []
    install_commands    = []
    compute_type        = "BUILD_GENERAL1_SMALL"
    create_codepipeline = false  # No pipeline needed for static media
    create             = true
    enable_oac         = true
    create_cloudfront  = true
    use_custom_buildspec = false
    enable_signed_cookies = true
    # Enable static website hosting
    enable_website = false  # CloudFront will serve the content
    index_document = ""
    error_document = ""
    # Error pages configuration for CloudFront
    error_pages = [
      {
        error_code = 403
        response_code = "200"
        response_page_path = "/error.html"
        error_caching_min_ttl = 0
      },
      {
        error_code = 404
        response_code = "200"
        response_page_path = "/error.html"
        error_caching_min_ttl = 0
      }
    ]
  }
}

# ECR (Container Registry)
create_ecr = true
ecr_repositories = ["apcer-api-dev"]

# RDS PostgreSQL
create_rds = true
rds_engine = "postgres"
rds_port = 5432
rds_force_ssl = false
rds_storage_type        = "gp3"
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
# Add your ACM certificate ARN here (must be in us-east-1 for CloudFront)
cloudfront_acm_certificate_arn = "arn:aws:acm:us-east-1:193363646479:certificate/4addba11-4204-403f-834e-97174519f67e"

# =============================================================================
# CI/CD SERVICES
# =============================================================================

# CodePipeline
create_codepipelines = true
version_control_type = "github"
# CodeBuild
create_codebuild = true

# ===================
# SERVERLESS MICROSERVICES
# ===================
serverless_microservices_codepipeline = {
  serverless_service-1 = {
    service_name          = "document-svc"
    repository_path       = "APCER-Life-Sciences-Inc/pv-tool-document-svc"
    repository_branch     = "main"
    node_version          = "22.17.0"
    bucket_path           = "microservices/document-microservice/dev"
    install_commands      = ["npm install -g serverless"]
    build_commands    = [
      "yarn cache clean",
      "yarn install"
    ]
  } 
}

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
create_security = false
synthetics = {
  api_health_check = {
    name        = "api-health"
    target_url  = "https://api-test.apcerls.com/health"
    schedule    = "rate(5 minutes)"
    timeout     = 30
    memory_size = 128
  }
  admin_health_check = {
    name        = "admin-health"
    target_url  = "https://admin-test.apcerls.com/health"
    schedule    = "rate(5 minutes)"
    timeout     = 30
    memory_size = 128
  }
}


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