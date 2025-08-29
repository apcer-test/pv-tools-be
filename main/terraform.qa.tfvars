region = "us-east-2"
project_name = "apcer"
env = "dev"
app_name = "apcer-app"

# VPC variables
create_vpc = true
cidr = "10.10.0.0/16"
vpc_availability_zones = ["us-east-2a", "us-east-2b", "us-east-2c"]
create_database_subnet_group = true

# ALB variables
alb_enable_deletion_protection = false

# RDS Database variables
create_rds_database = true

# RDS Configuration
rds_instance_class      = "db.t3.micro"
rds_allocated_storage   = 20
rds_max_allocated_storage = 100
rds_storage_type        = "gp3"
rds_engine            = "postgres"
rds_engine_version    = "16.4"
rds_port              = 5432
rds_force_ssl         = false  # SSL not forced for now
rds_backup_retention_period = 7

# RDS Schedule Configuration
rds_backup_window       = "03:00-04:00"
rds_maintenance_window  = "sun:04:00-sun:05:00"

# S3 Configuration
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
s3_folder_paths = ["logs", "temp", "uploads"]
s3_microservices = ["user-service", "notification-service", "workflow-service"]
s3_service_folders = ["admin", "api", "media"]
s3_tags = {
  Environment = "dev"
  Project     = "apcer"
  Service     = "storage"
}



###S3 Bucket ECOSYSTEM        
storage_buckets = {
  env_bucket = {
    service_name        = "env"
    enable_versioning   = true
    service_folders     = ["admin", "api"]
    lifecycle_rules     = []
  }
  codepipeline_artifacts_bucket = {
    service_name        = "codepipeline-artifacts"
    lifecycle_rules     = []
  }
}

# Frontend Configuration
frontends = {
  admin = {
    service_name         = "admin"
    domain              = "admin-test.webelight.co.in"
    repository_path     = "webelight/riddhi-gsp/riddhi-gsp-admin"
    repository_branch   = "main"
    bucket_path         = "admin/dev"
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
  }
  media = {
    service_name         = "media"
    domain              = "media-test.webelight.co.in"
    repository_path     = ""
    repository_branch   = "main"
    bucket_path         = "media/dev"
    node_version        = "20.9.0"
    build_commands      = []
    install_commands    = []
    compute_type        = "BUILD_GENERAL1_SMALL"
    create_codepipeline = false
    create             = true
    enable_oac         = true
  }
}

serverless_microservices_codepipeline = {
  serverless_service-1 = {
    service_name          = "document-svc"
    repository_path       = "webelight/microservices/document-microservice"
    repository_branch     = "main"
    node_version          = "22.17.0"
    bucket_path           = "microservices/document-microservice/dev"
    install_commands      = ["npm install -g serverless"]
    build_commands    = [
      "yarn cache clean",
      "yarn install"
    ]
  }
  # serverless_service-2 = {
  #   service_name          = "notification-queue-svc"
  #   repository_path       = "webelight/microservices/notification-queue-handler"
  #   repository_branch     = "master"
  #   node_version          = "20.9.0"
  #   bucket_path           = "microservices/notification-queue-handler/dev"
  #   install_commands      = ["npm install -g serverless"]
  #   build_commands        = ["yarn install"]
  # }
}


# ECS ECOSYSTEM
create_ecs_ecosystem = true

# ECS Services Configuration - Moved to terraform.dev.tfvars
# services = {}

# CodePipeline Configuration
create_codepipelines = true

# CloudTrail Configuration
create_cloudtrail = true

# Security Configuration
create_security = true

known_ip_addresses = [
  "192.168.1.0/24",
  "10.0.0.0/16",
  "203.0.113.0/24"
]




# Cognito Configuration
create_cognito = true
cognito_callback_urls = [
  "https://admin.webelight.co.in/callback",
  "https://api.webelight.co.in/callback"
]
cognito_logout_urls = [
  "https://admin.webelight.co.in/logout",
  "https://api.webelight.co.in/logout"
]
create_bastion = true
bastion_allowed_cidrs = [
  "192.168.1.0/24",
  "10.10.0.0/16",
  "203.0.113.0/24"
]

# SES Configuration
# create_ses = true
# ses_domain_name = "webelight.co.in"

# SNS Configuration
# create_sns = true
# sns_topic_name = "notifications"
# sns_subscriptions = {
#   email_notifications = {
#     protocol = "email"
#     endpoint = "admin@webelight.co.in"
#   }
# }

# SQS Configuration
# create_sqs = true
# sqs_queue_name = "messages"
# sqs_create_dead_letter_queue = true

# AWS Backup Configuration
create_aws_backup = true
aws_backup_vault_name = "apcer-backup-vault-dev"
aws_backup_plan_name = "apcer-backup-plan-dev"
aws_backup_schedule = "cron(0 5 * * ? *)"
aws_backup_retention_days = 35
aws_backup_selection_name = "apcer-backup-selection-dev"
aws_backup_resource_arns = [
  # Additional resource ARNs can be added here
  # The module will automatically include RDS, ECS, and ElastiCache resources
  # based on what's created in your infrastructure
]

# AWS Backup Lifecycle Configuration
aws_backup_cold_storage_after_days = 30
aws_backup_enable_long_term_retention = true
aws_backup_long_term_schedule = "cron(0 5 1 * ? *)"  # Monthly on 1st at 5 AM UTC
aws_backup_long_term_retention_days = 365
aws_backup_long_term_cold_storage_after_days = 90

# CloudFront Configuration
cloudfront_acm_certificate_arn = "arn:aws:acm:us-east-1:912106457730:certificate/11da5ef2-0995-4549-b889-12a81d9d1ece"

# CloudWatch Synthetics Configuration
create_synthetics = true
synthetics = {
  api_health_check = {
    name        = "api-health"
    target_url  = "https://api-test.webelight.co.in/health"
    schedule    = "rate(5 minutes)"
    timeout     = 30
    memory_size = 128
  }
  admin_health_check = {
    name        = "admin-health"
    target_url  = "https://admin-test.webelight.co.in/health"
    schedule    = "rate(5 minutes)"
    timeout     = 30
    memory_size = 128
  }
}

# ElastiCache Redis Configuration
create_elasticache = true

# AWS Budgets Configuration
create_aws_budgets = true
aws_budgets = {
  budget_type = "COST"
  budget_limit_amount = "900"
  budget_limit_unit = "USD"
  budget_time_unit = "MONTHLY"
  cost_filters = {
    # Filter by service if needed
    # "Service" = ["Amazon Elastic Compute Cloud", "Amazon Relational Database Service"]
  }
  budget_notifications = [
    {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 80
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = ["devops@webelight.co.in"]
      subscriber_sns_topic_arns  = []
    },
    {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 100
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = ["devops@webelight.co.in"]
      subscriber_sns_topic_arns  = []
    },
    {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 120
      threshold_type             = "PERCENTAGE"
      notification_type          = "FORECASTED"
      subscriber_email_addresses = ["devops@webelight.co.in"]
      subscriber_sns_topic_arns  = []
    }
  ]
  create_budget_alarm = true
  alarm_evaluation_periods = 1
  alarm_period = 86400  # 24 hours
  create_sns_topic = true
  subscriber_email_addresses = ["devops@webelight.co.in"]
}

# AWS VPN Configuration
create_aws_vpn = false  # Set to true when you need VPN
aws_vpn = {
  create_client_vpn = false
  create_site_to_site_vpn = false
  client_vpn_cidr_block = "172.31.0.0/16"
  client_vpn_subnet_ids = [
    # Add your private subnet IDs here when needed
    # module.vpc[0].private_subnet_ids[0]
  ]
  client_vpn_authorized_networks = [
    "10.10.0.0/16",  # VPC CIDR
    "172.31.0.0/16"  # Client VPN CIDR
  ]
  client_vpn_domain = "vpn.webelight.co.in"
  split_tunnel = true
  enable_connection_logging = false
  log_retention_days = 30
  customer_gateways = {
    # Example Site-to-Site VPN configuration
    # office = {
    #   bgp_asn = 65000
    #   ip_address = "203.0.113.10"
    #   static_routes_only = true
    #   static_routes = ["192.168.1.0/24", "192.168.2.0/24"]
    # }
  }
}