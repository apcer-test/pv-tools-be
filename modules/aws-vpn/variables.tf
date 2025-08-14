# AWS VPN Module Variables

variable "create_client_vpn" {
  description = "Whether to create Client VPN endpoint"
  type        = bool
  default     = false
}

variable "create_site_to_site_vpn" {
  description = "Whether to create Site-to-Site VPN"
  type        = bool
  default     = false
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "env" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for VPN resources"
  type        = string
}

# Client VPN Variables
variable "client_vpn_cidr_block" {
  description = "CIDR block for Client VPN clients"
  type        = string
  default     = "172.31.0.0/16"
}

variable "client_vpn_subnet_ids" {
  description = "List of subnet IDs for Client VPN network association"
  type        = list(string)
  default     = []
}

variable "client_vpn_authorized_networks" {
  description = "List of network CIDRs authorized for Client VPN access"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "client_vpn_domain" {
  description = "Domain name for Client VPN certificates"
  type        = string
  default     = "vpn.local"
}

variable "split_tunnel" {
  description = "Whether to enable split tunnel for Client VPN"
  type        = bool
  default     = true
}

variable "enable_connection_logging" {
  description = "Whether to enable connection logging for Client VPN"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain Client VPN logs"
  type        = number
  default     = 30
}

# Site-to-Site VPN Variables
variable "customer_gateways" {
  description = "Map of customer gateway configurations"
  type = map(object({
    bgp_asn           = number
    ip_address        = string
    static_routes_only = bool
    static_routes     = list(string)
  }))
  default = {}
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
} 