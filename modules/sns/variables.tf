# SNS Module Variables

variable "create_topic" {
  description = "Whether to create SNS topic"
  type        = bool
  default     = false
}

variable "create_platform_applications" {
  description = "Whether to create SNS platform applications"
  type        = bool
  default     = false
}

variable "create_platform_endpoints" {
  description = "Whether to create SNS platform endpoints"
  type        = bool
  default     = false
}

variable "topic_name" {
  description = "Name of the SNS topic"
  type        = string
  default     = "topic"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

# Topic configuration
variable "delivery_policy" {
  description = "SNS topic delivery policy"
  type        = string
  default     = null
}

variable "topic_policy" {
  description = "SNS topic policy"
  type        = string
  default     = null
}

variable "kms_master_key_id" {
  description = "KMS master key ID for encryption"
  type        = string
  default     = null
}

variable "fifo_topic" {
  description = "Whether this is a FIFO topic"
  type        = bool
  default     = false
}

variable "content_based_deduplication" {
  description = "Enable content-based deduplication"
  type        = bool
  default     = false
}

variable "data_protection_policy" {
  description = "SNS topic data protection policy"
  type        = string
  default     = null
}

# Subscriptions
variable "subscriptions" {
  description = "SNS topic subscriptions"
  type = map(object({
    protocol                        = string
    endpoint                        = string
    confirmation_timeout_in_minutes = optional(number)
    delivery_policy                 = optional(string)
    filter_policy                   = optional(string)
    filter_policy_scope             = optional(string)
    raw_message_delivery            = optional(bool)
    redrive_policy                  = optional(string)
    subscription_role_arn           = optional(string)
  }))
  default = {}
}

# Platform applications
variable "platform_applications" {
  description = "SNS platform applications"
  type = map(object({
    name                           = string
    platform                       = string
    platform_credential            = string
    platform_principal             = string
    event_delivery_failure_topic_arn = optional(string)
    event_endpoint_created_topic_arn = optional(string)
    event_endpoint_deleted_topic_arn = optional(string)
    event_endpoint_updated_topic_arn = optional(string)
    failure_feedback_role_arn      = optional(string)
    success_feedback_role_arn      = optional(string)
    success_feedback_sample_rate   = optional(number)
  }))
  default = {}
}

# Platform endpoints
variable "platform_endpoints" {
  description = "SNS platform endpoints"
  type = map(object({
    platform_application_arn = string
    token                   = string
    custom_user_data        = optional(string)
    enabled                 = optional(bool)
  }))
  default = {}
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
} 