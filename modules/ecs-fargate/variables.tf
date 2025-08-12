# ECS Fargate Module Variables

variable "create_ecs_cluster" {
  description = "Whether to create the ECS cluster"
  type        = bool
  default     = false
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "env" {
  description = "Environment name"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where ECS services will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS services"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Security group ID of the ALB"
  type        = string
}

variable "alb_target_group_arns" {
  description = "Map of ALB target group ARNs for each service"
  type        = map(string)
}

variable "ecs_execution_role_arn" {
  description = "ARN of the ECS execution role"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  type        = string
}

variable "ecr_repository_urls" {
  description = "Map of ECR repository URLs for each service"
  type        = map(string)
}

# Services Configuration - Main input for ECS services
variable "services" {
  description = "Map of services for ECS Fargate deployment"
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
    # Environment variables and secrets
    environment_variables = optional(list(object({
      name  = string
      value = string
    })), [])
    secrets = optional(list(object({
      name      = string
      valueFrom = string
    })), [])
    # X-Ray configuration
    enable_xray          = optional(bool, true)
    xray_daemon_cpu     = optional(number, 32)
    xray_daemon_memory  = optional(number, 256)
    # CodePipeline configuration (only used when create_codepipelines is true)
    service_name         = optional(string, "")  # Service name for pipeline and connection naming (e.g., "api-backend-service")
    repository_path      = optional(string, "")  # Full GitLab repository path (e.g., "webelight/api-backend-service")
    repository_branch    = optional(string, "main")
    bucket_path          = optional(string, "")  # S3 env bucket path for this service (e.g., "microservices/api/dev")
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