# S3 Bucket Outputs
output "s3_bucket_arns" {
  description = "ARNs of all S3 buckets"
  value = {
    for bucket_key, bucket in module.s3 : bucket_key => bucket.bucket_arn
  }
}

output "frontend_bucket_arn" {
  description = "ARN of the frontend S3 bucket"
  value = try(module.s3["frontend_bucket"].bucket_arn, "")
}



output "env_bucket_arn" {
  description = "ARN of the environment S3 bucket"
  value = try(module.s3["env_bucket"].bucket_arn, "")
}

# CloudFront Distribution Outputs
output "cloudfront_distribution_arns" {
  description = "ARNs of all CloudFront distributions"
  value = merge(
    {
      for cdn_key, cdn in module.cloudfront_s3 : cdn_key => cdn.cloudfront_distribution_arn
    },
    {
      for cdn_key, cdn in module.cloudfront_ecs : cdn_key => cdn.cloudfront_distribution_arn
    }
  )
}

output "frontend_cloudfront_arn" {
  description = "ARN of the frontend CloudFront distribution"
  value = try(module.cloudfront_s3["frontend-cloudfront"].cloudfront_distribution_arn, "")
}



output "api_cloudfront_arn" {
  description = "ARN of the API CloudFront distribution"
  value = try(module.cloudfront_ecs["service1-cloudfront"].cloudfront_distribution_arn, "")
}



# CloudFront Domain Names
output "cloudfront_domain_names" {
  description = "Domain names of all CloudFront distributions"
  value = merge(
    {
      for cdn_key, cdn in module.cloudfront_s3 : cdn_key => cdn.cloudfront_distribution_domain_name
    },
    {
      for cdn_key, cdn in module.cloudfront_ecs : cdn_key => cdn.cloudfront_distribution_domain_name
    }
  )
}

output "frontend_cloudfront_domain" {
  description = "Domain name of the frontend CloudFront distribution"
  value = try(module.cloudfront_s3["frontend-cloudfront"].cloudfront_distribution_domain_name, "")
}



# S3 Bucket Names
output "s3_bucket_names" {
  description = "Names of all S3 buckets"
  value = {
    for bucket_key, bucket in module.s3 : bucket_key => bucket.bucket_name
  }
}

output "frontend_bucket_name" {
  description = "Name of the frontend S3 bucket"
  value = try(module.s3["frontend_bucket"].bucket_name, "")
}



# ElastiCache Redis Outputs
output "redis_replication_group_id" {
  description = "ID of the Redis replication group"
  value       = var.create_elasticache ? module.elasticache[0].redis_replication_group_id : ""
}

output "redis_primary_endpoint" {
  description = "Primary endpoint of the Redis cluster"
  value       = var.create_elasticache ? module.elasticache[0].redis_primary_endpoint : ""
}

output "redis_reader_endpoint" {
  description = "Reader endpoint of the Redis cluster"
  value       = var.create_elasticache ? module.elasticache[0].redis_reader_endpoint : ""
}

output "redis_port" {
  description = "Port of the Redis cluster"
  value       = try(module.elasticache[0].redis_port, "")
}

# AWS Budgets Outputs
output "budget_id" {
  description = "ID of the AWS Budget"
  value       = try(module.aws_budgets[0].budget_id, "")
}

output "budget_arn" {
  description = "ARN of the AWS Budget"
  value       = try(module.aws_budgets[0].budget_arn, "")
}

output "budget_name" {
  description = "Name of the AWS Budget"
  value       = try(module.aws_budgets[0].budget_name, "")
}

output "budget_notifications" {
  description = "Budget notification configurations"
  value       = try(module.aws_budgets[0].budget_notifications, [])
}

output "budget_cloudwatch_alarm_names" {
  description = "Names of the CloudWatch alarms for budget monitoring"
  value       = try(module.aws_budgets[0].cloudwatch_alarm_names, [])
}

output "budget_sns_topic_arn" {
  description = "ARN of the SNS topic for budget notifications"
  value       = try(module.aws_budgets[0].sns_topic_arn, "")
}

output "budget_sns_topic_name" {
  description = "Name of the SNS topic for budget notifications"
  value       = try(module.aws_budgets[0].sns_topic_name, "")
}

output "budget_configuration" {
  description = "Complete budget configuration"
  value       = try(module.aws_budgets[0].budget_configuration, {})
}

# AWS Backup Outputs
output "backup_vault_arn" {
  description = "ARN of the AWS Backup vault"
  value       = try(module.aws_backup[0].vault_arn, "")
}

output "backup_vault_name" {
  description = "Name of the AWS Backup vault"
  value       = try(module.aws_backup[0].vault_name, "")
}

output "backup_plan_name" {
  description = "Name of the AWS Backup plan"
  value       = try(module.aws_backup[0].plan_name, "")
}

output "backup_selection_name" {
  description = "Name of the AWS Backup selection"
  value       = try(module.aws_backup[0].selection_name, "")
}

output "backup_resource_arns" {
  description = "List of resource ARNs being backed up"
  value       = try(local.backup_resource_arns, [])
}

output "backup_configuration" {
  description = "Complete backup configuration"
  value = var.create_aws_backup ? {
    vault_name     = var.aws_backup_vault_name
    plan_name      = var.aws_backup_plan_name
    schedule       = var.aws_backup_schedule
    retention_days = var.aws_backup_retention_days
    resource_count = length(local.backup_resource_arns)
    resources      = local.backup_resource_arns
    lifecycle = {
      cold_storage_after_days = var.aws_backup_cold_storage_after_days
      enable_long_term_retention = var.aws_backup_enable_long_term_retention
      long_term_schedule = var.aws_backup_long_term_schedule
      long_term_retention_days = var.aws_backup_long_term_retention_days
      long_term_cold_storage_after_days = var.aws_backup_long_term_cold_storage_after_days
    }
  } : null
}

# AWS VPN Outputs
output "client_vpn_endpoint_id" {
  description = "ID of the Client VPN endpoint"
  value       = try(module.aws_vpn[0].client_vpn_endpoint_id, "")
}

output "client_vpn_endpoint_dns_name" {
  description = "DNS name of the Client VPN endpoint"
  value       = try(module.aws_vpn[0].client_vpn_endpoint_dns_name, "")
}

output "vpn_gateway_id" {
  description = "ID of the VPN Gateway"
  value       = try(module.aws_vpn[0].vpn_gateway_id, "")
}

output "vpn_connections" {
  description = "Map of VPN connection configurations"
  value       = try(module.aws_vpn[0].vpn_connections, {})
}

output "vpn_configuration" {
  description = "Complete VPN configuration summary"
  value       = try(module.aws_vpn[0].vpn_configuration, {})
}

# CodePipeline Outputs

# Bastion Host Outputs
output "bastion_instance_id" {
  description = "ID of the bastion host instance"
  value       = try(module.ec2-bastion[0].instance_id, "")
}

output "bastion_public_ip" {
  description = "Public IP address of the bastion host"
  value       = try(module.ec2-bastion[0].elastic_ip, "")
}

output "bastion_admin_private_key" {
  description = "Private key for admin access to bastion host (save as .pem file)"
  value       = try(module.ec2-bastion[0].admin_private_key, "")
  sensitive   = true
}

output "bastion_developer_private_key" {
  description = "Private key for developer tunnel access to bastion host (save as .pem file)"
  value       = try(module.ec2-bastion[0].developer_private_key, "")
  sensitive   = true
}

output "bastion_connection_info" {
  description = "Complete connection information for bastion host"
  value       = try(module.ec2-bastion[0].connection_info, {})
}

output "bastion_ssh_command" {
  description = "SSH command to connect to bastion host (admin access)"
  value       = try(module.ec2-bastion[0].ssh_connection_command, "")
}

output "bastion_tunnel_command" {
  description = "SSH tunnel command for RDS database access"
  value       = try(module.ec2-bastion[0].tunnel_connection_command, "")
}

# PEM File Outputs (for direct copying)
output "admin_key_pem" {
  description = "Admin private key in PEM format (copy this to a .pem file)"
  value       = try(module.ec2-bastion[0].admin_private_key, "")
  sensitive   = true
}

output "developer_key_pem" {
  description = "Developer private key in PEM format (copy this to a .pem file)"
  value       = try(module.ec2-bastion[0].developer_private_key, "")
  sensitive   = true
}

# Quick commands to save PEM files
output "save_admin_key_command" {
  description = "Command to save admin key to PEM file"
  value       = try("terraform output -raw admin_key_pem > admin-key.pem && chmod 600 admin-key.pem", "")
}

output "save_developer_key_command" {
  description = "Command to save developer key to PEM file"
  value       = try("terraform output -raw developer_key_pem > developer-key.pem && chmod 600 developer-key.pem", "")
}
