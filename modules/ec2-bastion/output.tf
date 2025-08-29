# EC2 Bastion Host Module Outputs

output "instance_id" {
  description = "ID of the bastion host instance"
  value       = var.create_bastion ? aws_instance.bastion[0].id : null
}

output "instance_arn" {
  description = "ARN of the bastion host instance"
  value       = var.create_bastion ? aws_instance.bastion[0].arn : null
}

output "instance_private_ip" {
  description = "Private IP address of the bastion host"
  value       = var.create_bastion ? aws_instance.bastion[0].private_ip : null
}

output "instance_public_ip" {
  description = "Public IP address of the bastion host (from instance)"
  value       = var.create_bastion ? aws_instance.bastion[0].public_ip : null
}

output "elastic_ip" {
  description = "Elastic IP address of the bastion host"
  value       = var.create_bastion ? aws_eip.bastion_eip[0].public_ip : null
}

output "elastic_ip_allocation_id" {
  description = "Allocation ID of the Elastic IP"
  value       = var.create_bastion ? aws_eip.bastion_eip[0].allocation_id : null
}

output "instance_state" {
  description = "State of the bastion host instance"
  value       = var.create_bastion ? aws_instance.bastion[0].instance_state : null
}

output "admin_key_name" {
  description = "Name of the admin SSH key"
  value       = var.create_bastion ? module.ssh_keys.admin_key_name : null
}

output "developer_key_name" {
  description = "Name of the developer SSH key"
  value       = var.create_bastion ? module.ssh_keys.developer_key_name : null
}

output "admin_private_key" {
  description = "Private key for admin access (save this to a .pem file)"
  value       = var.create_bastion ? module.ssh_keys.admin_private_key : null
  sensitive   = false
}

output "developer_private_key" {
  description = "Private key for developer tunnel access (save this to a .pem file)"
  value       = var.create_bastion ? module.ssh_keys.developer_private_key : null
  sensitive   = false
}

output "security_groups" {
  description = "List of security group IDs attached to the bastion host"
  value       = var.create_bastion ? aws_instance.bastion[0].vpc_security_group_ids : []
}

output "ssh_connection_command" {
  description = "SSH command to connect to bastion host (for admin access)"
  value       = var.create_bastion ? "ssh -i ${module.ssh_keys.admin_key_name}.pem ubuntu@${aws_eip.bastion_eip[0].public_ip}" : null
}

output "tunnel_connection_command" {
  description = "SSH tunnel command for RDS database access"
  value       = var.create_bastion ? "ssh -i ${module.ssh_keys.developer_key_name}.pem -L 5432:RDS_ENDPOINT:5432 developer@${aws_eip.bastion_eip[0].public_ip} -N" : null
}

output "connection_info" {
  description = "Complete connection information"
  value = var.create_bastion ? {
    bastion_ip              = aws_eip.bastion_eip[0].public_ip
    admin_user             = "ubuntu"
    tunnel_user            = "developer"
    admin_key_name         = module.ssh_keys.admin_key_name
    developer_key_name     = module.ssh_keys.developer_key_name
    rds_tunnel_port        = 5432
    admin_ssh_command      = "ssh -i ${module.ssh_keys.admin_key_name}.pem ubuntu@${aws_eip.bastion_eip[0].public_ip}"
    rds_tunnel_command     = "ssh -i ${module.ssh_keys.developer_key_name}.pem -L 5432:RDS_ENDPOINT:5432 developer@${aws_eip.bastion_eip[0].public_ip} -N"
    pgadmin_host          = aws_eip.bastion_eip[0].public_ip
    pgadmin_username      = "developer"
    note                  = "Replace RDS_ENDPOINT with your actual RDS endpoint"
  } : null
} 