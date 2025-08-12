# VPC module outputs 

# VPC outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = var.create_vpc ? aws_vpc.vpc[0].id : null
}

output "vpc_arn" {
  description = "ARN of the VPC"
  value       = var.create_vpc ? aws_vpc.vpc[0].arn : null
}

# Subnet outputs
output "public_subnet_ids" {
  description = "List of IDs of public subnets"
  value       = [for subnet in aws_subnet.public_subnet : subnet.id]
}

output "private_subnet_ids" {
  description = "List of IDs of private subnets"
  value       = [for subnet in aws_subnet.private_subnet : subnet.id]
}

output "database_subnet_ids" {
  description = "List of IDs of database subnets"
  value       = [for subnet in aws_subnet.database_subnet : subnet.id]
}

# DB Subnet Group outputs
output "database_subnet_group_name" {
  description = "Name of the database subnet group"
  value       = var.create_vpc && var.create_database_subnet_group ? aws_db_subnet_group.default[0].name : null
}

output "database_subnet_group_id" {
  description = "ID of the database subnet group"
  value       = var.create_vpc && var.create_database_subnet_group ? aws_db_subnet_group.default[0].id : null
}

# NAT Gateway outputs
output "nat_gateway_public_ip" {
  description = "Public Elastic IP of NAT Gateway"
  value       = length(local.private_subnet_cidrs) > 0 ? aws_eip.nat[0].public_ip : null
}