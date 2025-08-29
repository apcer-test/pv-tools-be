# AWS Backup Configuration
# Creates backup vault, plan, and selection for disaster recovery

# AWS Backup Module
module "aws_backup" {
  count  = var.create_aws_backup ? 1 : 0
  source = "../modules/aws-backup"

  # Vault configuration
  vault_name = var.aws_backup_vault_name
  kms_key_arn = null  # Use AWS managed key for encryption

  # Plan configuration
  plan_name = var.aws_backup_plan_name
  rule_name = "daily-backup-rule"
  schedule  = var.aws_backup_schedule
  start_window = 60      # 1 hour start window
  completion_window = 180 # 3 hour completion window
  retention_days = var.aws_backup_retention_days

  # Lifecycle configuration
  cold_storage_after_days = var.aws_backup_cold_storage_after_days
  delete_after_days = null      # Use retention_days instead
  enable_long_term_retention = var.aws_backup_enable_long_term_retention
  long_term_schedule = var.aws_backup_long_term_schedule
  long_term_retention_days = var.aws_backup_long_term_retention_days
  long_term_cold_storage_after_days = var.aws_backup_long_term_cold_storage_after_days

  # Selection configuration
  selection_name = var.aws_backup_selection_name
  resource_arns  = local.backup_resource_arns
  selection_tag_key   = "Backup"
  selection_tag_value = "true"

  # Project configuration
  project_name = var.project_name
  env          = var.env

  # Tags
  tags = {
    Name        = "${var.project_name}-${var.env}-backup"
    Project     = var.project_name
    Service     = "aws-backup"
    Environment = var.env
    Terraform   = "true"
  }

  # Recovery point tags
  recovery_point_tags = {
    Project     = var.project_name
    Environment = var.env
    BackupType  = "automated"
  }
}

# Local values for backup resource ARNs
locals {
  # Collect resource ARNs for backup
  backup_resource_arns = concat(
    # RDS Database ARNs
    var.create_rds ? [module.rds[0].db_instance_arn] : [],
    
    # ECS Service ARNs (if ECS ecosystem is created)
    var.create_ecs_ecosystem ? [
      for service in module.ecs_fargate[0].ecs_service_arns : service
    ] : [],
    

    
    # ElastiCache Redis ARN
    var.create_elasticache ? [module.elasticache[0].redis_replication_group_arn] : [],
    
    # Manual resource ARNs from tfvars
    var.aws_backup_resource_arns
  )
} 