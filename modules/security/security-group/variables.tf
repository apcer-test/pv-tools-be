# Security Groups module input variables

variable "create_security_group" {
  description = "Whether to create security group"
  type        = bool
  default     = false
}

variable "security_group_name" {
  description = "Name of the security group"
  type        = string
}

variable "security_group_description" {
  description = "Description of the security group"
  type        = string
  default     = ""
}

variable "vpc_id" {
  description = "VPC ID where the security group will be created"
  type        = string
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
  description = "Additional tags for the security group"
  type        = map(string)
  default     = {}
}

# Rule Type Conditionals
variable "use_cidr_rules" {
  description = "Whether to apply CIDR-based rules"
  type        = bool
  default     = false
}

variable "use_sg_rules" {
  description = "Whether to apply Security Group-based rules"
  type        = bool
  default     = false
}

# Ingress Rules with CIDR blocks
variable "ingress_rules_cidr" {
  description = "List of ingress rules with CIDR blocks"
  type = list(object({
    from_port   = number
    to_port     = number
    protocol    = string
    description = string
    cidr_blocks = string
  }))
  default = []
}

# Ingress Rules with Security Group sources
variable "ingress_rules_sg" {
  description = "List of ingress rules with security group sources"
  type = list(object({
    from_port                = number
    to_port                  = number
    protocol                 = string
    description              = string
    source_security_group_id = string
  }))
  default = []
}

# Egress Rules with CIDR blocks
variable "egress_rules_cidr" {
  description = "List of egress rules with CIDR blocks"
  type = list(object({
    from_port   = number
    to_port     = number
    protocol    = string
    description = string
    cidr_blocks = string
  }))
  default = []
}

# Egress Rules with Security Group sources
variable "egress_rules_sg" {
  description = "List of egress rules with security group sources"
  type = list(object({
    from_port                = number
    to_port                  = number
    protocol                 = string
    description              = string
    source_security_group_id = string
  }))
  default = []
} 