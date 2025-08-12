# Security Groups module outputs

output "security_group_id" {
  description = "ID of the security group"
  value       = var.create_security_group ? aws_security_group.security_group[0].id : null
}

output "security_group_arn" {
  description = "ARN of the security group"
  value       = var.create_security_group ? aws_security_group.security_group[0].arn : null
}

output "security_group_name" {
  description = "Name of the security group"
  value       = var.create_security_group ? aws_security_group.security_group[0].name : null
}