variable "vault_name" {
  description = "Name of the AWS Backup vault"
  type        = string
  default     = "main-backup-vault"
}

variable "kms_key_arn" {
  description = "KMS key ARN for backup vault encryption"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags for the backup vault"
  type        = map(string)
  default     = {}
}

variable "plan_name" {
  description = "Name of the backup plan"
  type        = string
  default     = "main-backup-plan"
}

variable "rule_name" {
  description = "Name of the backup rule"
  type        = string
  default     = "daily-backup-rule"
}

variable "schedule" {
  description = "CRON schedule for backup (default: daily at 5am UTC)"
  type        = string
  default     = "cron(0 5 * * ? *)"
}

variable "start_window" {
  description = "Start window in minutes"
  type        = number
  default     = 60
}

variable "completion_window" {
  description = "Completion window in minutes"
  type        = number
  default     = 180
}

variable "retention_days" {
  description = "Retention period in days"
  type        = number
  default     = 35
}

variable "recovery_point_tags" {
  description = "Tags for recovery points"
  type        = map(string)
  default     = {}
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "selection_name" {
  description = "Name of the backup selection"
  type        = string
  default     = "main-backup-selection"
}

variable "resource_arns" {
  description = "List of ARNs of resources to back up"
  type        = list(string)
  default     = []
}

variable "selection_tag_key" {
  description = "Tag key for resource selection"
  type        = string
  default     = "Backup"
}

variable "selection_tag_value" {
  description = "Tag value for resource selection"
  type        = string
  default     = "true"
} 