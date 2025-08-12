# ECR Module Variables

variable "create_ecr_repositories" {
  description = "Whether to create ECR repositories"
  type        = bool
  default     = false
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "env" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "ecr_repositories" {
  description = "List of ECR repository configurations"
  type = list(object({
    name                = string
    retention_count     = number
    force_delete        = bool
    scan_on_push        = bool
  }))
  default = []
}

variable "tags" {
  description = "Additional tags for ECR repositories"
  type        = map(string)
  default     = {}
} 