# EC2 Bastion Host Module Variables

variable "create_bastion" {
  description = "Whether to create the bastion host"
  type        = bool
  default     = false
}

variable "create_admin_key" {
  description = "Whether to create admin SSH key for bastion host"
  type        = bool
  default     = true
}

variable "create_developer_key" {
  description = "Whether to create developer SSH key for tunnel access"
  type        = bool
  default     = true
}

variable "bastion_name" {
  description = "Name of the bastion host"
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

variable "ami_id" {
  description = "AMI ID for the bastion host (Ubuntu 22.04 LTS)"
  type        = string
  default     = ""
}

variable "instance_type" {
  description = "Instance type for the bastion host"
  type        = string
  default     = "t3.micro"
}

variable "subnet_id" {
  description = "Subnet ID where bastion host will be created (public subnet)"
  type        = string
}

variable "vpc_security_group_ids" {
  description = "List of security group IDs for the bastion host"
  type        = list(string)
}

variable "volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 20
}

variable "enable_instance_scheduler" {
  description = "Whether to enable instance scheduler"
  type        = bool
  default     = false
}

variable "disable_api_termination" {
  description = "Whether to enable termination protection for the bastion host"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags for the bastion host"
  type        = map(string)
  default     = {}
} 