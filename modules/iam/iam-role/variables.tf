# IAM Role Module Variables

variable "create_iam_role" {
  description = "Whether to create IAM role"
  type        = bool
  default     = false
}

variable "iam_role_name" {
  description = "Name of IAM role"
  type        = string
}

variable "iam_role_description" {
  description = "IAM Role description"
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

variable "tags" {
  description = "Additional tags for the IAM role"
  type        = map(string)
  default     = {}
}

# Trust Relationships
variable "trusted_role_services" {
  description = "List of AWS service names that can assume this role (e.g., ['codepipeline.amazonaws.com', 'ecs-tasks.amazonaws.com'])"
  type        = list(string)
  default     = []
}

# Policy Attachments
variable "custom_role_policy_arns" {
  description = "List of ARNs of IAM policies to attach to IAM role"
  type        = list(string)
  default     = []
}

variable "additional_policy_arns" {
  description = "Additional policy ARNs to attach (e.g., custom policies created via modules)"
  type        = list(string)
  default     = []
} 