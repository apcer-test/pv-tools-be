# ALB Module Variables - Flexible Services Configuration

variable "create_alb" {
  description = "Whether to create the ALB"
  type        = bool
  default     = false
}

variable "alb_name" {
  description = "Name of the Application Load Balancer"
  type        = string
}

variable "alb_internal" {
  description = "Whether the ALB is internal or internet-facing"
  type        = bool
  default     = false
}

variable "alb_security_groups" {
  description = "List of security group IDs for the ALB"
  type        = list(string)
}

variable "alb_public_subnet_ids" {
  description = "List of public subnet IDs for the ALB"
  type        = list(string)
}

variable "alb_vpc_id" {
  description = "VPC ID where the ALB will be created"
  type        = string
}

variable "alb_enable_deletion_protection" {
  description = "Whether to enable deletion protection for the ALB"
  type        = bool
  default     = true
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "env" {
  description = "Environment name"
  type        = string
}

# Services Configuration - Main input for ALB target groups and listeners
variable "services" {
  description = "Map of services for ALB target groups and listeners"
  type = map(object({
    container_name      = string
    container_port      = number
    domain              = string
    health_check_path   = string
    expose_via_alb      = optional(bool, true)
  }))
  default = {}
} 