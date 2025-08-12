# SSH Keys Module Variables

variable "create_admin_key" {
  description = "Whether to create admin SSH key"
  type        = bool
  default     = false
}

variable "create_developer_key" {
  description = "Whether to create developer SSH key"
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

variable "admin_key_name" {
  description = "Name for the admin SSH key pair"
  type        = string
  default     = ""
}

variable "developer_key_name" {
  description = "Name for the developer tunnel SSH key pair"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags for the SSH keys"
  type        = map(string)
  default     = {}
} 