# Global variables
variable "region" {
  type    = string
}

variable "project_name" {
  type    = string
}

variable "env" {
  type    = string
}

# VPC variables
variable "create_vpc" { 
  type    = bool
}

variable "cidr" {
  type    = string
}

variable "availability_zones" {
  type    = list(string)
}

variable "create_database_subnet_group" {
  type    = bool
}

variable "services" {
  description = "Master configuration for ECS services"
  type = map(object({
    container_name       = string
    container_port       = number
    health_check_path    = string
    cpu                  = number
    memory               = number
    domain               = string
    # Optional fields with sensible defaults
    desired_count        = optional(number, 1)
    image_tag            = optional(string, "latest")
    priority             = optional(number, 100)
    command              = optional(list(string), [])
    # Auto-scaling configuration
    enable_auto_scaling  = optional(bool, true)
    min_capacity         = optional(number, 1)
    max_capacity         = optional(number, 10)
    target_cpu_utilization = optional(number, 70)
    target_memory_utilization = optional(number, 80)
    # CodePipeline configuration (only used when create_codepipelines is true)
    service_name         = optional(string, "")  # Service name for pipeline and connection naming (e.g., "api-backend-service")
    repository_path      = optional(string, "")  # Full GitLab repository path (e.g., "webelight/api-backend-service")
    repository_branch    = optional(string, "main")
    bucket_path          = optional(string, "")  # S3 env bucket path for this service (e.g., "microservices/api/dev")
    env_bucket_path      = optional(string, "")  # Environment-specific S3 bucket path for this service (e.g., "api/dev")
    compute_type         = optional(string, "BUILD_GENERAL1_SMALL")  # CodeBuild compute type
    
    # CloudFront Configuration (ALB origin)
    create_cloudfront    = optional(bool, false)
    cloudfront_aliases   = optional(list(string), [])  # If empty, automatically uses 'domain' field
    cloudfront_forwarded_values = optional(object({
      query_string = bool
      headers      = list(string)
      cookies = object({
        forward = string
      })
    }), {
      query_string = true
      headers      = ["*"]
      cookies = {
        forward = "all"
      }
    })
  }))
  default = {}
}




# RDS Database variables
variable "create_rds" {
  description = "Whether to create RDS database"
  type        = bool
  default     = false
}

variable "create_rds_database" {
  type    = bool
}

variable "rds_allocated_storage" {
  type    = number
}
variable "rds_engine" {
  description = "Database engine"
  type        = string
}

variable "rds_engine_version" {
  description = "Database engine version"
  type        = string
}

variable "rds_force_ssl" {
  description = "Force SSL connections for RDS"
  type        = bool
}

variable "rds_port" {
  description = "Port for RDS"
  type        = number
}

variable "rds_instance_class" {
  description = "Instance class for RDS"
  type        = string
}

variable "rds_max_allocated_storage" {
  description = "Maximum allocated storage for RDS"
  type        = number
}

variable "rds_storage_type" {
  description = "Storage type for RDS"
  type        = string
}

variable "rds_backup_window" {
  description = "Backup window for RDS"
  type        = string
}

variable "rds_maintenance_window" {
  description = "Maintenance window for RDS"
  type        = string
}

variable "rds_backup_retention_period" {
  description = "Backup retention period for RDS"
  type        = number
}

variable "rds_username" {
  description = "Username for the master DB user"
  type        = string
}

variable "rds_database_name" {
  description = "Name of the database to create"
  type        = string
}

variable "rds_manage_master_user_secret" {
  description = "Whether to manage the master user secret in AWS Secrets Manager"
  type        = bool
  default     = false
}

variable "rds_master_user_secret_kms_key_id" {
  description = "The KMS key ID to use for encrypting the master user secret"
  type        = string
  default     = null
}




variable "databases" {
  description = "Master configuration for all database instances"
  type = map(object({
    instance_name        = string
    instance_class       = string
    allocated_storage    = number
    engine              = string
    engine_version      = string
    port                = number
    db_name             = string
    username            = string
    multi_az            = optional(bool, false)
    backup_retention    = optional(number, 7)
    storage_encrypted   = optional(bool, true)
    create              = optional(bool, true)
  }))
  default = {}
}


# s3 variables
variable "create_s3_buckets" {
  description = "Flag to determine whether to create S3 buckets"
  type        = bool
}
variable "frontends" {
  description = "Master configuration for all frontend buckets"
  type = map(object({
    service_name       = string  # "admin", "media", "api", etc.
    domain            = optional(string, "")
    repository_path   = optional(string, "")
    repository_branch = optional(string, "main")
    bucket_path       = optional(string, "")
    node_version      = optional(string, "20.9.0")
    build_commands    = optional(list(string), [])
    install_commands  = optional(list(string), [])
    compute_type      = optional(string, "BUILD_GENERAL1_SMALL")
    create_codepipeline = optional(bool, false)
    create_cloudfront = optional(bool, true)
    enable_website     = optional(bool, false)
    enable_versioning  = optional(bool, true)
    enable_encryption  = optional(bool, true)
    cors_rules         = optional(list(object({
      allowed_methods = list(string)
      allowed_origins = list(string)
    })), [])  # Headers and max_age are auto-configured with sensible defaults
    lifecycle_rules    = optional(list(object({
      id                         = string
      enabled                    = optional(bool, true)
      filter_prefix              = optional(string, "")
      expiration_days            = optional(number, 0)
      noncurrent_version_expiration_days = optional(number, 0)
      transition_to_ia_days      = optional(number, 0)
      transition_to_glacier_days = optional(number, 0)
    })), [])
    microservices      = optional(list(string), [])
    # environments will be auto-generated based on var.env
    service_folders    = optional(list(string), [])
    enable_oac         = optional(bool, true)   # Enable Origin Access Control for CloudFront
    create             = optional(bool, true)
  }))
  default = {}
}
variable "microservices" {
  description = "Master configuration for all microservices"
  type = map(object({
    service_name       = string  # "admin", "media", "api", etc.
    enable_website     = optional(bool, false)
    enable_versioning  = optional(bool, true)
    enable_encryption  = optional(bool, true)
    cors_rules         = optional(list(object({
      allowed_methods = list(string)
      allowed_origins = list(string)
    })), [])  # Headers and max_age are auto-configured with sensible defaults
  }))
  default = {}
}
variable "environments" {
  description = "List of environments for service and microservice folders"
  type        = list(string)
  default     = ["dev", "staging", "prod"]
}

variable "s3_index_document" {
  description = "Index document for S3 bucket"
  type        = string
}

variable "s3_error_document" {
  description = "Error document for S3 bucket"
  type        = string
}

variable "s3_acl" {
  description = "ACL for S3 bucket"
  type        = string
}

variable "s3_cors_rules" {
  description = "CORS rules for S3 bucket"
  type        = list(object({
    allowed_methods = list(string)
    allowed_origins = list(string)
  }))
}
variable "s3_lifecycle_rules" {
  description = "Lifecycle rules for S3 bucket"
  type        = list(object({
    id                         = string
    enabled                    = optional(bool, true)
    filter_prefix              = optional(string, "")
    expiration_days            = optional(number, 0)
    noncurrent_version_expiration_days = optional(number, 0)
    transition_to_ia_days      = optional(number, 0)
    transition_to_glacier_days = optional(number, 0)
  }))
}
variable "s3_folder_paths" {
  description = "List of general folders to create in the S3 bucket"
  type        = list(string)
}


variable "app_name" {
  description = "Name of the application"
  type        = string
}
variable "s3_tags" {
  description = "Tags for S3 bucket"
  type        = map(string)
}
variable "s3_service_folders" {
  description = "List of service folders to create with environment subfolders"
  type        = list(string)
}
variable "s3_microservices" {
  description = "List of microservices to create under microservices/ folder"
  type        = list(string)
}
variable "create_ecs_ecosystem" {
  description = "Flag to determine whether to create ECS ecosystem"
  type        = bool
}

# storage buckets variables
variable "storage_buckets" {
  description = "Master configuration for all S3 buckets"
  type = map(object({
    service_name       = string  # "admin", "media", "api", etc.
    enable_website     = optional(bool, false)
    enable_versioning  = optional(bool, true)
    enable_encryption  = optional(bool, true)
    cors_rules         = optional(list(object({
      allowed_methods = list(string)
      allowed_origins = list(string)
    })), [])  # Headers and max_age are auto-configured with sensible defaults
    lifecycle_rules    = optional(list(object({
      id                         = string
      enabled                    = optional(bool, true)
      filter_prefix              = optional(string, "")
      expiration_days            = optional(number, 0)
      noncurrent_version_expiration_days = optional(number, 0)
      transition_to_ia_days      = optional(number, 0)
      transition_to_glacier_days = optional(number, 0)
    })), [])
    microservices      = optional(list(string), [])
    # environments will be auto-generated based on var.env
    service_folders    = optional(list(string), [])
    enable_oac         = optional(bool, true)   # Enable Origin Access Control for CloudFront
    create             = optional(bool, true)
  }))
  default = {}
}

# Master CodePipeline Configuration
variable "codepipelines" {
  description = "Master configuration for all CodePipelines"
  type = map(object({
    pipeline_type        = string  # "admin", "ecs"
    service_name         = string  # "admin", "api", "notification", etc.
    enable_build_stage   = optional(bool, false)
    enable_ecr_build_stage = optional(bool, true)
    enable_ecs_deploy_stage = optional(bool, true)
    enable_invalidate_stage = optional(bool, false)
    repo_path           = string
    repo_branch         = optional(string, "main")
    codestart_connection_name = string
    container_name      = optional(string, "")
    s3_bucket_name     = optional(string, "")
    env_vars           = optional(list(object({
      name  = string
      value = string
    })), [])
    build_compute_type  = optional(string, "BUILD_GENERAL1_MEDIUM")
    create             = optional(bool, true)
  }))
  default = {}
}

variable "create_codepipelines" {
  description = "Flag to determine whether to create CodePipelines"
  type        = bool
  default     = false
}

variable "create_iam_role_codepipeline" {
  description = "Flag to determine whether to create IAM role for CodePipeline"
  type        = bool
  default     = true
}

variable "commit_buildspec_to_gitlab" {
  description = "Flag to determine whether to commit buildspec.yml files to GitLab repositories"
  type        = bool
  default     = false
}

variable "skip_if_buildspec_exists" {
  description = "Skip creating buildspec.yml if it already exists in the repository"
  type        = bool
  default     = true
}

variable "auto_commit_buildspec" {
  description = "Automatically commit buildspec files to GitLab with sensible defaults (replaces manual flag management)"
  type        = bool
  default     = false
}

# variable "gitlab_token" {
#   description = "GitLab API token for committing buildspec files (required if commit_buildspec_to_gitlab is true)"
#   type        = string
#   default     = ""
#   sensitive   = true
# }

variable "force_terraform_buildspec" {
  description = "Force use of Terraform-generated buildspec even if buildspec.yml exists in repository"
  type        = bool
  default     = false
}

variable "use_custom_buildspec" {
  description = "Whether to use a custom buildspec from the repository"
  type        = bool
  default     = false
}

# Version control type for CodePipeline
variable "version_control_type" {
  description = "Type of version control system (gitlab-self-hosted, gitlab-com, github)"
  type        = string
  default     = "gitlab-com"
  
  validation {
    condition     = contains(["gitlab-self-hosted", "gitlab-com", "github"], var.version_control_type)
    error_message = "Repository type must be one of: gitlab-self-hosted, gitlab-com, github."
  }
}

# GitLab configuration
# variable "gitlab_token" {
#   description = "GitLab access token for CodePipeline"
#   type        = string
#   default     = ""
#   sensitive   = true
# }

# GitHub configuration
variable "github_token" {
  description = "GitHub Personal Access Token for CodePipeline connections"
  type        = string
  default     = ""
  sensitive   = true
}



# EC2 Bastion variables
variable "create_bastion" {
  description = "Flag to determine whether to create bastion host"
  type        = bool
  default     = false
}


variable "bastion_allowed_cidrs" {
  description = "List of CIDR blocks allowed to access bastion"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "bastion_ami_id" {
  description = "AMI ID for bastion host"
  type        = string
  default     = ""
}

variable "bastion_instance_type" {
  description = "Instance type for bastion host"
  type        = string
  default     = "t3.micro"
}

variable "bastion_volume_size" {
  description = "Volume size for bastion host"
  type        = number
  default     = 20
}

variable "bastion_enable_instance_scheduler" {
  description = "Enable instance scheduler for bastion"
  type        = bool
  default     = false
}

variable "bastion_disable_api_termination" {
  description = "Disable API termination for bastion"
  type        = bool
  default     = false
}

variable "bastion_security_group_ids" {
  description = "Additional security group IDs for bastion host"
  type        = list(string)
  default     = []
}

# CloudTrail variables
variable "create_cloudtrail" {
  description = "Flag to determine whether to create CloudTrail"
  type        = bool
  default     = false
}

# Security variables
variable "create_security" {
  description = "Flag to determine whether to create security services"
  type        = bool
  default     = false
}

variable "blocked_ip_addresses" {
  description = "List of IP addresses to block in WAF"
  type        = list(string)
  default     = []
}

variable "known_ip_addresses" {
  description = "List of known IP addresses to allow in WAF"
  type        = list(string)
  default     = []
}





# Cognito variables
variable "create_cognito" {
  description = "Whether to create Cognito resources"
  type        = bool
  default     = false
}

variable "cognito_password_minimum_length" {
  description = "Minimum password length for Cognito"
  type        = number
  default     = 8
}

variable "cognito_password_require_lowercase" {
  description = "Require lowercase in Cognito password"
  type        = bool
  default     = true
}

variable "cognito_password_require_numbers" {
  description = "Require numbers in Cognito password"
  type        = bool
  default     = true
}

variable "cognito_password_require_symbols" {
  description = "Require symbols in Cognito password"
  type        = bool
  default     = true
}

variable "cognito_password_require_uppercase" {
  description = "Require uppercase in Cognito password"
  type        = bool
  default     = true
}

variable "cognito_callback_urls" {
  description = "Callback URLs for Cognito user pool client"
  type        = list(string)
  default     = []
}

variable "cognito_logout_urls" {
  description = "Logout URLs for Cognito user pool client"
  type        = list(string)
  default     = []
}

variable "cognito_allow_unauthenticated_identities" {
  description = "Allow unauthenticated identities in Cognito"
  type        = bool
  default     = false
}

variable "cognito_authenticated_role_policy_statements" {
  description = "IAM policy statements for authenticated Cognito users"
  type        = list(any)
  default     = [
    {
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ]
      Resource = [
        "arn:aws:s3:::user-bucket/*"
      ]
    }
  ]
}

variable "cognito_unauthenticated_role_policy_statements" {
  description = "IAM policy statements for unauthenticated Cognito users"
  type        = list(any)
  default     = [
    {
      Effect = "Allow"
      Action = [
        "s3:GetObject"
      ]
      Resource = [
        "arn:aws:s3:::public-bucket/*"
      ]
    }
  ]
}





# ElastiCache Redis Configuration
variable "create_elasticache" {
  description = "Whether to create ElastiCache Redis cluster"
  type        = bool
  default     = false
}

# Master CDN Configuration
variable "cloudfront_acm_certificate_arn" {
  description = "ACM certificate ARN for CloudFront distributions (must be in us-east-1). Leave empty for automatic wildcard certificate detection based on domain aliases"
  type        = string
  default     = ""
}

variable "cdn_distributions" {
  description = "Master configuration for all CloudFront distributions"
  type = map(object({
    service_name         = string  # "admin", "api", "media", etc.
    origin_type          = string  # "s3", "alb", "custom"
    origin_domain_name   = optional(string, "")  # Auto-generated based on origin_type
    origin_id            = optional(string, "")
    origin_path          = optional(string, "")
    protocol_policy      = optional(string, "http-only")
    aliases              = optional(list(string), [])
    certificate_arn      = optional(string, "")
    default_root_object  = optional(string, "index.html")
    price_class          = optional(string, "PriceClass_100")
    error_pages          = optional(list(object({
      error_code            = number
      response_code         = string
      response_page_path    = string
      error_caching_min_ttl = number
    })), [])
    default_cache_behavior = optional(object({
      target_origin_id       = string
      viewer_protocol_policy = string
      allowed_methods        = list(string)
      cached_methods         = list(string)
      compress               = bool
      min_ttl                = number
      default_ttl            = number
      max_ttl                = number
      forwarded_values = object({
        query_string = bool
        headers      = list(string)
        cookies = object({
          forward = string
        })
      })
    }), null)
    forwarded_values = optional(object({
      query_string = bool
      headers      = list(string)
      cookies = object({
        forward = string
      })
    }), null)
    create               = optional(bool, true)
  }))
  default = {}
}

# ALB variables
variable "alb_enable_deletion_protection" {
  description = "Whether to enable deletion protection for the ALB"
  type        = bool
  default     = false
}

# AWS Backup variables
variable "create_aws_backup" {
  description = "Whether to create AWS Backup vault and plan"
  type        = bool
  default     = false
}

variable "aws_backup_vault_name" {
  description = "Name of the AWS Backup vault"
  type        = string
  default     = ""
}

variable "aws_backup_plan_name" {
  description = "Name of the AWS Backup plan"
  type        = string
  default     = ""
}

variable "aws_backup_schedule" {
  description = "CRON schedule for AWS Backup"
  type        = string
  default     = "cron(0 5 * * ? *)"
}

variable "aws_backup_retention_days" {
  description = "Retention period in days for AWS Backup"
  type        = number
  default     = 35
}

variable "aws_backup_selection_name" {
  description = "Name of the AWS Backup selection"
  type        = string
  default     = ""
}

variable "aws_backup_resource_arns" {
  description = "List of resource ARNs to back up"
  type        = list(string)
  default     = []
}

# AWS Backup Lifecycle variables
variable "aws_backup_cold_storage_after_days" {
  description = "Number of days after which to move backups to cold storage"
  type        = number
  default     = 30
}

variable "aws_backup_enable_long_term_retention" {
  description = "Whether to enable long-term retention rule"
  type        = bool
  default     = true
}

variable "aws_backup_long_term_schedule" {
  description = "CRON schedule for long-term retention backups"
  type        = string
  default     = "cron(0 5 1 * ? *)"  # Monthly on 1st at 5 AM UTC
}

variable "aws_backup_long_term_retention_days" {
  description = "Retention period in days for long-term backups"
  type        = number
  default     = 365
}

variable "aws_backup_long_term_cold_storage_after_days" {
  description = "Number of days after which to move long-term backups to cold storage"
  type        = number
  default     = 90
}

# Serverless microservices CodePipeline configuration
variable "serverless_microservices_codepipeline" {
  description = "Configuration for serverless microservices CodePipelines"
  type = map(object({
    service_name       = string
    repository_path    = string
    repository_branch  = string
    bucket_path        = string
    node_version       = string
    build_commands     = list(string)
    install_commands   = list(string)
    compute_type       = optional(string, "BUILD_GENERAL1_SMALL")
  }))
  default = {}
}

# CloudWatch Synthetics Configuration
variable "create_synthetics" {
  description = "Whether to create CloudWatch Synthetics canaries"
  type        = bool
  default     = false
}

variable "synthetics" {
  description = "Configuration for CloudWatch Synthetics canaries"
  type = object({
    api_health_check = object({
      name        = string
      target_url  = string
      schedule    = string
      timeout     = number
      memory_size = number
    })
    admin_health_check = object({
      name        = string
      target_url  = string
      schedule    = string
      timeout     = number
      memory_size = number
    })
  })
}

# AWS Budgets Configuration
variable "create_aws_budgets" {
  description = "Whether to create AWS Budgets with monitoring and alerts"
  type        = bool
  default     = false
}

variable "aws_budgets" {
  description = "Configuration for AWS Budgets"
  type = object({
    budget_type = optional(string, "COST")
    budget_limit_amount = optional(string, "100")
    budget_limit_unit = optional(string, "USD")
    budget_time_unit = optional(string, "MONTHLY")
    cost_filters = optional(map(list(string)), {})
    budget_notifications = optional(list(object({
      comparison_operator        = string
      threshold                  = number
      threshold_type             = string
      notification_type          = string
      subscriber_email_addresses = list(string)
      subscriber_sns_topic_arns  = optional(list(string), [])
    })), [])
    create_budget_alarm = optional(bool, true)
    alarm_evaluation_periods = optional(number, 1)
    alarm_period = optional(number, 86400)
    create_sns_topic = optional(bool, true)
    subscriber_email_addresses = optional(list(string), [])
  })
  default = {
    budget_type = "COST"
    budget_limit_amount = "100"
    budget_limit_unit = "USD"
    budget_time_unit = "MONTHLY"
    cost_filters = {}
    budget_notifications = []
    create_budget_alarm = true
    alarm_evaluation_periods = 1
    alarm_period = 86400
    create_sns_topic = true
    subscriber_email_addresses = []
  }
}

# AWS VPN Configuration
variable "create_aws_vpn" {
  description = "Whether to create AWS VPN resources"
  type        = bool
  default     = false
}

variable "aws_vpn" {
  description = "Configuration for AWS VPN"
  type = object({
    create_client_vpn = optional(bool, false)
    create_site_to_site_vpn = optional(bool, false)
    client_vpn_cidr_block = optional(string, "172.31.0.0/16")
    client_vpn_subnet_ids = optional(list(string), [])
    client_vpn_authorized_networks = optional(list(string), ["0.0.0.0/0"])
    client_vpn_domain = optional(string, "vpn.local")
    split_tunnel = optional(bool, true)
    enable_connection_logging = optional(bool, false)
    log_retention_days = optional(number, 30)
    customer_gateways = optional(map(object({
      bgp_asn           = number
      ip_address        = string
      static_routes_only = bool
      static_routes     = list(string)
    })), {})
  })
  default = {
    create_client_vpn = false
    create_site_to_site_vpn = false
    client_vpn_cidr_block = "172.31.0.0/16"
    client_vpn_subnet_ids = []
    client_vpn_authorized_networks = ["0.0.0.0/0"]
    client_vpn_domain = "vpn.local"
    split_tunnel = true
    enable_connection_logging = false
    log_retention_days = 30
    customer_gateways = {}
  }
}