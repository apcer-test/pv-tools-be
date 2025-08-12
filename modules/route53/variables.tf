# Route53 Module Variables

variable "create_hosted_zone" {
  description = "Whether to create a Route53 hosted zone"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain name for the hosted zone"
  type        = string
}

variable "zone_id" {
  description = "Zone ID of existing hosted zone (used when create_hosted_zone is false)"
  type        = string
  default     = ""
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "env" {
  description = "Environment name"
  type        = string
}

variable "a_records" {
  description = "Map of A records to create"
  type = map(object({
    name    = string
    ttl     = number
    records = list(string)
  }))
  default = {}
}

variable "cname_records" {
  description = "Map of CNAME records to create"
  type = map(object({
    name   = string
    ttl    = number
    record = string
  }))
  default = {}
}

variable "mx_records" {
  description = "Map of MX records to create"
  type = map(object({
    name    = string
    ttl     = number
    records = list(string)
  }))
  default = {}
}

variable "txt_records" {
  description = "Map of TXT records to create"
  type = map(object({
    name    = string
    ttl     = number
    records = list(string)
  }))
  default = {}
}

variable "alias_records" {
  description = "Map of alias records to create"
  type = map(object({
    name                   = string
    type                   = string
    alias_name             = string
    alias_zone_id          = string
    evaluate_target_health = bool
  }))
  default = {}
}

variable "health_checks" {
  description = "Map of health checks to create"
  type = map(object({
    fqdn              = string
    port              = number
    type              = string
    resource_path     = string
    failure_threshold = number
    request_interval  = number
  }))
  default = {}
}

variable "failover_records" {
  description = "Map of failover records to create"
  type = map(object({
    name            = string
    type            = string
    ttl             = number
    set_identifier  = string
    health_check_id = string
    failover_type   = string
    records         = list(string)
  }))
  default = {}
} 