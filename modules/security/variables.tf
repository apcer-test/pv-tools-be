# Security Module Variables

variable "create_aws_config" {
  description = "Whether to create AWS Config"
  type        = bool
  default     = false
}

variable "create_guardduty" {
  description = "Whether to create GuardDuty"
  type        = bool
  default     = false
}

variable "create_waf" {
  description = "Whether to create WAF"
  type        = bool
  default     = false
}

variable "create_inspector" {
  description = "Whether to create AWS Inspector"
  type        = bool
  default     = false
}

variable "create_security_hub" {
  description = "Whether to create AWS Security Hub"
  type        = bool
  default     = false
}

variable "enable_finding_aggregator" {
  description = "Whether to enable Security Hub finding aggregator"
  type        = bool
  default     = false
}

variable "finding_aggregator_excluded_regions" {
  description = "List of regions to exclude from Security Hub finding aggregator"
  type        = list(string)
  default     = []
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

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
} 