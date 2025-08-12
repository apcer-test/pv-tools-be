# S3 Module Variables

# Basic Configuration
variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "app_name" {
  description = "Name of the application"
  type        = string
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

# Website Configuration
variable "enable_website" {
  description = "Enable static website hosting"
  type        = bool
  default     = false
}

variable "index_document" {
  description = "Index document for website hosting"
  type        = string
  default     = "index.html"
}

variable "error_document" {
  description = "Error document for website hosting"
  type        = string
  default     = "error.html"
}

# Security Configuration
variable "enable_encryption" {
  description = "Enable S3 bucket encryption"
  type        = bool
  default     = true
}

variable "enable_versioning" {
  description = "Enable S3 bucket versioning"
  type        = bool
  default     = true
}

variable "block_public_access" {
  description = "Enable S3 bucket public access block"
  type        = bool
  default     = true
}

# ACL Configuration
variable "enable_acl" {
  description = "Enable S3 bucket ACL"
  type        = bool
  default     = false
}

variable "acl" {
  description = "S3 bucket ACL"
  type        = string
  default     = "private"
}

# CORS Configuration
variable "enable_cors" {
  description = "Enable CORS configuration"
  type        = bool
  default     = false
}

variable "cors_rules" {
  description = "CORS configuration rules"
  type = list(object({
    allowed_headers = list(string)
    allowed_methods = list(string)
    allowed_origins = list(string)
    expose_headers  = list(string)
    max_age_seconds = number
  }))
  default = []
}

# Lifecycle Configuration
variable "enable_lifecycle" {
  description = "Enable lifecycle configuration"
  type        = bool
  default     = false
}

variable "lifecycle_rules" {
  description = "Lifecycle configuration rules"
  type = list(object({
    id                         = string
    enabled                    = optional(bool, true)
    filter_prefix              = optional(string, "")
    expiration_days            = optional(number, 0)
    noncurrent_version_expiration_days = optional(number, 0)
    transition_to_ia_days      = optional(number, 0)
    transition_to_glacier_days = optional(number, 0)
  }))
  default = []
}

# Folder Structure Configuration
variable "folder_paths" {
  description = "List of general folders to create in the S3 bucket"
  type        = list(string)
  default     = []
}

variable "service_folders" {
  description = "List of service folders to create with environment subfolders"
  type        = list(string)
  default     = []
}

variable "microservices" {
  description = "List of microservices to create under microservices/ folder"
  type        = list(string)
  default     = []
}

variable "environments" {
  description = "List of environments for service and microservice folders"
  type        = list(string)
  default     = ["dev", "staging", "prod"]
}

# Tags
variable "tags" {
  description = "A map of tags to assign to the resource"
  type        = map(string)
  default     = {}
}

# OAC Configuration
variable "enable_oac" {
  description = "Enable Origin Access Control for CloudFront"
  type        = bool
  default     = false
}

 