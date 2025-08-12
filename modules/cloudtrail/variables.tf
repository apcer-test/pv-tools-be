# CloudTrail Module Variables

variable "create_cloudtrail" {
  description = "Whether to create CloudTrail trail"
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

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group for CloudTrail logs"
  type        = string
  default     = null
}

variable "cloudtrail_cloudwatch_role_arn" {
  description = "ARN of the IAM role for CloudTrail to CloudWatch integration"
  type        = string
  default     = null
}

variable "cloudtrail_s3_bucket_name" {
  description = "Name of the S3 bucket for CloudTrail logs"
  type        = string
} 