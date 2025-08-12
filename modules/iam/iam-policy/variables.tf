# IAM Policy Module Variables

# General Configuration
variable "create_iam_policy" {
  description = "Flag to determine whether to create the IAM policy"
  type        = bool
  default     = true
}

variable "iam_policy_name" {
  description = "Name of the IAM policy"
  type        = string
}

variable "description" {
  description = "Description of the IAM policy"
  type        = string
  default     = ""
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "env" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = ""
}

variable "account_id" {
  description = "AWS account ID"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags to apply to the IAM policy"
  type        = map(string)
  default     = {}
}

# Policy Attachment Flags
variable "attach_cloudwatch_policy" {
  description = "Whether to attach CloudWatch policy"
  type        = bool
  default     = false
}

variable "attach_rds_policy" {
  description = "Whether to attach RDS policy"
  type        = bool
  default     = false
}

variable "attach_s3_bucket_policy" {
  description = "Whether to attach S3 bucket policy"
  type        = bool
  default     = false
}

variable "attach_cloudfront_access" {
  description = "Whether to attach CloudFront invalidation policy"
  type        = bool
  default     = false
}

variable "attach_lambda_access" {
  description = "Whether to attach Lambda access policy"
  type        = bool
  default     = false
}

variable "attach_iam_role" {
  description = "Whether to attach IAM role management policy"
  type        = bool
  default     = false
}

variable "attach_ecr_policy" {
  description = "Whether to attach ECR policy"
  type        = bool
  default     = false
}

variable "attach_ecs_policy" {
  description = "Whether to attach ECS policy"
  type        = bool
  default     = false
}

variable "attach_ssm_policy" {
  description = "Whether to attach Systems Manager (SSM) policy"
  type        = bool
  default     = false
}

variable "attach_sqs_policy" {
  description = "Whether to attach Simple Queue Service (SQS) policy"
  type        = bool
  default     = false
}

variable "attach_sns_policy" {
  description = "Whether to attach Simple Notification Service (SNS) policy"
  type        = bool
  default     = false
}

variable "attach_codebuild_policy" {
  description = "Whether to attach CodeBuild policy"
  type        = bool
  default     = false
}

variable "attach_codepipeline_policy" {
  description = "Whether to attach CodePipeline policy"
  type        = bool
  default     = false
}

variable "attach_secrets_manager_policy" {
  description = "Whether to attach Secrets Manager policy"
  type        = bool
  default     = false
}

variable "attach_api_gateway_policy" {
  description = "Whether to attach API Gateway policy"
  type        = bool
  default     = false
}

variable "attach_cloudformation_policy" {
  description = "Whether to attach CloudFormation policy"
  type        = bool
  default     = false
}

# Resource-specific Variables
variable "database_name" {
  description = "RDS database name for RDS policy"
  type        = string
  default     = ""
}

variable "cloudfront_distribution_arn" {
  description = "CloudFront distribution ARN for invalidation policy"
  type        = string
  default     = ""
} 