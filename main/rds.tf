

# RDS Database Configuration
# Creates RDS database with static naming and environment-based backup retention

locals {
  # Environment-based backup retention
  rds_backup_retention = (
    contains(["dev", "qa"], var.env) ? 4 :
    var.env == "uat" ? 5 :
    var.env == "prod" ? 7 :
    4  # Default fallback
  )
  
  # First availability zone for RDS placement
  rds_first_az = var.availability_zones[0]
}

# AWS RDS will automatically create and manage the secret

# Custom RDS Parameter Group with configurable SSL
resource "aws_db_parameter_group" "rds_parameter_group" {
  count  = var.create_rds ? 1 : 0
  family = var.rds_engine == "postgres" ? "postgres16" : "mysql8.0"
  name   = "${var.project_name}-db-params-${var.env}"

  parameter {
    name         = var.rds_engine == "postgres" ? "rds.force_ssl" : "require_secure_transport"
    value        = var.rds_force_ssl ? "1" : "0"
    apply_method = var.rds_engine == "postgres" ? "pending-reboot" : "immediate"
  }

  tags = {
    Name        = "${var.project_name}-db-params-${var.env}"
    Project     = var.project_name
    Environment = var.env
    Terraform   = "true"
  }
}

# RDS Database Instance
module "rds" {
  count  = var.create_rds ? 1 : 0
  source = "../modules/rds"
  
  # Required basic variables (non-prefixed)
  allocated_storage    = var.rds_allocated_storage
  engine              = var.rds_engine
  engine_version      = var.rds_engine_version
  instance_class      = var.rds_instance_class
  db_name             = "test"     # Static database name
  username            = "master"   # Static master username
  db_subnet_group_name = module.vpc.database_subnet_group_name
  vpc_security_group_ids = [module.rds-sg[0].security_group_id]
  
  # RDS-prefixed variables
  rds_instance_name           = "${var.project_name}-db-${var.env}"
  rds_instance_class          = var.rds_instance_class
  rds_allocated_storage       = var.rds_allocated_storage
  rds_max_allocated_storage   = var.rds_max_allocated_storage
  rds_storage_type            = var.rds_storage_type
  rds_engine                  = var.rds_engine
  rds_engine_version          = var.rds_engine_version
  rds_port                    = var.rds_port
  rds_db_name                 = var.rds_database_name
  rds_master_db_user          = var.rds_username
  rds_manage_master_user_secret = var.rds_manage_master_user_secret
  rds_master_user_secret_kms_key_id = var.rds_master_user_secret_kms_key_id
  rds_security_group_id       = [module.rds-sg[0].security_group_id]
  rds_db_subnet_group_name    = module.vpc.database_subnet_group_name
  rds_availability_zone       = local.rds_first_az
  rds_backup_window           = var.rds_backup_window
  rds_backup_retention_period = local.rds_backup_retention
  rds_maintenance_window      = var.rds_maintenance_window
  rds_parameter_group_name    = aws_db_parameter_group.rds_parameter_group[0].name
  
  # Required tagging
  project_name = var.project_name
  env          = var.env
  name         = var.project_name
  app          = var.project_name
  
  # No dependencies needed - AWS handles secret creation
}

# AWS automatically updates the secret with RDS endpoint - no manual intervention needed 