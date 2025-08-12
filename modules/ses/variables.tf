# SES Module Variables

variable "create_domain_identity" {
  description = "Whether to create SES domain identity"
  type        = bool
  default     = false
}

variable "create_email_identities" {
  description = "Whether to create SES email identities"
  type        = bool
  default     = false
}

variable "create_configuration_set" {
  description = "Whether to create SES configuration set"
  type        = bool
  default     = false
}

variable "create_receipt_rule_set" {
  description = "Whether to create SES receipt rule set"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain name for SES identity"
  type        = string
  default     = ""
}

variable "email_identities" {
  description = "List of email addresses for SES identities"
  type        = list(string)
  default     = []
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for DNS records"
  type        = string
  default     = ""
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

# Configuration set variables
variable "delivery_options" {
  description = "SES delivery options"
  type = object({
    tls_policy = string
  })
  default = null
}

variable "reputation_metrics_enabled" {
  description = "Enable reputation metrics"
  type        = bool
  default     = true
}

variable "sending_enabled" {
  description = "Enable sending"
  type        = bool
  default     = true
}

# Event destinations
variable "event_destinations" {
  description = "SES event destinations"
  type = map(object({
    cloudwatch_destination = optional(object({
      default_value  = string
      dimension_name = string
      value_source   = string
    }))
    kinesis_destination = optional(object({
      role_arn   = string
      stream_arn = string
    }))
    sns_destination = optional(object({
      topic_arn = string
    }))
    matching_event_types = list(string)
  }))
  default = {}
}

# Receipt rules
variable "receipt_rules" {
  description = "SES receipt rules"
  type = map(object({
    recipients = list(string)
    enabled    = bool
    scan_enabled = bool
    tls_policy  = string
    s3_action = optional(object({
      bucket_name       = string
      object_key_prefix = string
      topic_arn         = string
    }))
    sns_action = optional(object({
      topic_arn = string
    }))
    lambda_action = optional(object({
      function_arn    = string
      invocation_type = string
    }))
    bounce_action = optional(object({
      message         = string
      sender          = string
      smtp_reply_code = string
      status_code     = string
      topic_arn       = string
    }))
    stop_action = optional(object({
      scope     = string
      topic_arn = string
    }))
    add_header_action = optional(object({
      header_name  = string
      header_value = string
    }))
    workmail_action = optional(object({
      organization_arn = string
      topic_arn        = string
    }))
  }))
  default = {}
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
} 