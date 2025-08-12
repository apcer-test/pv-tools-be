# VPC module input variables 


# Project name
variable "project_name" {
  description = "The project name"
  type        = string
}

# Environment (e.g., dev, prod)
variable "env" {
  description = "The environment (e.g., dev, prod)"
  type        = string
}

# Variable to control whether to create the VPC
variable "create_vpc" {
  description = "Flag to determine whether to create the VPC"
  type        = bool
}

# CIDR block for the VPC
variable "cidr" {
  description = "CIDR block for the VPC"
  type        = string
}


# List of availability zones to use for the subnets
variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

# Database subnet group creation
variable "create_database_subnet_group" {
  description = "Flag to determine whether to create the DB subnet group"
  type        = bool
}