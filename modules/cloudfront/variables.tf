# CloudFront Module Variables

# Basic Configuration
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

variable "enabled" {
  description = "Whether to enable this CloudFront distribution"
  type        = bool
  default     = true
}

variable "create_origin_access_control" {
  description = "Whether to create Origin Access Control (for S3 origins)"
  type        = bool
  default     = false
}

variable "is_website_endpoint" {
  description = "Whether the origin is a website endpoint (requires custom origin config)"
  type        = bool
  default     = false
}

variable "cloudfront_distribution_name" {
  description = "Name of the CloudFront distribution"
  type        = string
}

# Domain and Certificate Configuration
variable "aliases" {
  description = "List of alternate domain names (CNAMEs) for the distribution"
  type        = list(string)
  default     = []
}

variable "viewer_certificate_arn" {
  description = "ACM certificate ARN for custom domain"
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN (alternative name)"
  type        = string
  default     = ""
}

variable "alternate_domain_names" {
  description = "Alternate domain names for the distribution"
  type        = list(string)
  default     = []
}

# Origin Configuration
variable "origin_domain_name" {
  description = "Domain name of the origin (S3 bucket or ALB)"
  type        = string
}

variable "origin_id" {
  description = "Unique identifier for the origin"
  type        = string
}

variable "origin_path" {
  description = "Path that CloudFront appends to origin requests"
  type        = string
  default     = ""
}

variable "origin_protocol_policy" {
  description = "Origin protocol policy (http-only, https-only, match-viewer)"
  type        = string
  default     = "http-only"
}

# Distribution Settings
variable "default_root_object" {
  description = "Object that CloudFront returns when a user requests the root URL"
  type        = string
  default     = "index.html"
}

variable "price_class" {
  description = "Price class for the distribution (PriceClass_All, PriceClass_100, PriceClass_200)"
  type        = string
  default     = "PriceClass_100"
}

variable "comment" {
  description = "Comment for the distribution"
  type        = string
  default     = ""
}

# Error Pages Configuration
variable "error_pages" {
  description = "List of custom error response configurations"
  type = list(object({
    error_code         = number
    response_code      = number
    response_page_path = string
  }))
  default = []
}

# Cache Behavior Configuration
variable "default_cache_behavior" {
  description = "Default cache behavior configuration"
  type = object({
    target_origin_id       = string
    viewer_protocol_policy = string
    allowed_methods        = list(string)
    cached_methods         = list(string)
    compress               = bool
    min_ttl                = number
    default_ttl            = number
    max_ttl                = number
  })
  default = null
}

# Forwarded Values Configuration
variable "forwarded_values" {
  description = "Forwarded values configuration for cache behavior"
  type = object({
    query_string = bool
    headers      = list(string)
    cookies = object({
      forward           = string
      whitelisted_names = optional(list(string), [])
    })
  })
  default = null
}

# WAF Configuration
variable "web_acl_arn" {
  description = "ARN of the WAF Web ACL to associate with CloudFront"
  type        = string
  default     = ""
}

# Response Headers Policy Configuration
variable "response_headers_policy_id" {
  description = "ID of the response headers policy to associate with the distribution"
  type        = string
  default     = ""
}

# Tags
variable "tags" {
  description = "A map of tags to assign to the resource"
  type        = map(string)
  default     = {}
} 