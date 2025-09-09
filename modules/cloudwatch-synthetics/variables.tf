# CloudWatch Synthetics Module Variables

variable "create_synthetics" {
  description = "Whether to create CloudWatch Synthetics canaries"
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

variable "synthetics_alarm_emails" {
  description = "List of email addresses to subscribe to CloudWatch Synthetics alarm notifications"
  type        = list(string)
}

variable "artifacts_bucket_arn" {
  description = "ARN of the S3 bucket for canary artifacts"
  type        = string
  default     = ""
}

variable "canaries" {
  description = "Map of canary configurations"
  type = map(object({
    name                = string
    runtime_version     = string
    start_canary        = bool
    schedule_expression = string
    timeout_in_seconds  = number
    memory_in_mb        = number
    active_tracing      = bool
    subnet_ids          = list(string)
    security_group_ids  = list(string)
    target_url          = string
  }))
  default = {}
}

variable "alarm_actions" {
  description = "List of ARNs to notify when alarm triggers"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
} 