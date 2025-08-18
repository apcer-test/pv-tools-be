# =============================================================================
# APCER Development Environment Configuration
# =============================================================================

# Environment Configuration
environment = "dev"
project_name = "apcer"
region = "eu-west-2"

# VPC Configuration
cidr = "10.10.0.0/16"
azs = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]
private_subnets = ["10.10.1.0/24", "10.10.2.0/24", "10.10.3.0/24"]
public_subnets = ["10.10.101.0/24", "10.10.102.0/24", "10.10.103.0/24"]

# =============================================================================
# CORE INFRASTRUCTURE SERVICES
# =============================================================================

# VPC
create_vpc = true

# Application Load Balancer
create_alb = true
alb_internal = false
alb_enable_deletion_protection = false

# =============================================================================
# COMPUTE SERVICES
# =============================================================================

# ECS Fargate
create_ecs = true
ecs_cluster_name = "apcer-dev-cluster"
ecs_services = {
  service1 = {
    name = "apcer-api-dev"
    cpu = 128
    memory = 256
    desired_count = 1
    max_count = 2
    min_count = 1
    container_port = 3000
    health_check_path = "/health"
    enable_xray = false
 
  }
  service4 = {
    name = "apcer-notification-svc-dev"
    cpu = 128
    memory = 256
    desired_count = 1
    max_count = 2
    min_count = 1
    container_port = 3001
    health_check_path = "/health"
    enable_xray = false
    # Environment variables will be fetched from .env files via CodePipeline from S3
  }
}

# EC2 Bastion Host
create_ec2_bastion = true
bastion_instance_type = "t3.micro"
bastion_key_name = "apcer-dev-bastion"

# =============================================================================
# STORAGE SERVICES
# =============================================================================

# S3 Buckets
create_s3 = true
s3_buckets = {
  admin = {
    name = "apcer-admin-dev"
    versioning = true
    encryption = true
    public_access_block = true
    cors_configuration = true
    lifecycle_rules = {
      delete_after_days = 90
    }
    enable_oac = true
    create = true
    create_codepipeline = true
    repository_path = "admin"
    build_commands = ["npm install", "npm run build"]
    deploy_commands = ["aws s3 sync dist/ s3://apcer-admin-dev --delete"]
  }
}

# ECR (Container Registry)
create_ecr = true
ecr_repositories = ["apcer-api-dev", "apcer-notification-svc-dev"]

# =============================================================================
# DATABASE SERVICES
# =============================================================================

# RDS PostgreSQL
create_rds = true
rds_instance_class = "db.t3.micro"
rds_allocated_storage = 20
rds_max_allocated_storage = 100
rds_multi_az = false
rds_backup_retention_period = 7
rds_backup_window = "03:00-04:00"
rds_maintenance_window = "sun:04:00-sun:05:00"
rds_deletion_protection = false
rds_skip_final_snapshot = true
rds_engine_version = "14.10"
rds_database_name = "apcer_dev"
rds_username = "apcer_admin"
# Password will be managed by AWS Secrets Manager
rds_manage_master_user_secret = true
rds_master_user_secret_kms_key_id = ""  # Leave empty to use default AWS managed key

# ElastiCache Redis
create_elasticache = true
elasticache_node_type = "cache.t3.micro"
elasticache_num_cache_nodes = 1
elasticache_parameter_group_family = "redis7"
elasticache_engine_version = "7.0"
elasticache_port = 6379
elasticache_auth_token = ""  # Leave empty for dev

# =============================================================================
# CONTENT DELIVERY
# =============================================================================

# CloudFront
create_cloudfront = true
cloudfront_price_class = "PriceClass_100"
cloudfront_acm_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/your-cert-id"  # Update with your cert ARN (must be in us-east-1 for CloudFront)

# =============================================================================
# SECURITY SERVICES
# =============================================================================

# Security Groups (Centralized)
create_security_groups = true

# =============================================================================
# MONITORING & OBSERVABILITY
# =============================================================================

# CloudWatch
create_cloudwatch = true

# =============================================================================
# CI/CD SERVICES
# =============================================================================

# CodePipeline
create_codepipelines = true
version_control_type = "github"
gitlab_token = ""
gitlab_self_hosted_url = ""

# CodeBuild
create_codebuild = true


# =============================================================================
# DISABLED SERVICES
# =============================================================================

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

# AWS Budgets (Disabled)
create_aws_budgets = false

# Cognito (Disabled)
create_cognito = false

# CloudTrail (Disabled)
create_cloudtrail = false

# =============================================================================
# TAGS
# =============================================================================

tags = {
  Environment = "dev"
  Project     = "apcer"
  Owner       = "dev-team"
  CostCenter  = "development"
  ManagedBy   = "terraform"
} 