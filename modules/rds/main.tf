# RDS module
# Creates RDS databases 
resource "aws_db_instance" "this" {
  identifier                  = var.rds_instance_name
  instance_class              = var.rds_instance_class
  allocated_storage           = var.rds_allocated_storage
  max_allocated_storage       = var.rds_max_allocated_storage
  storage_type                = var.rds_storage_type
  engine                      = var.rds_engine
  engine_version              = var.rds_engine_version
  port                        = var.rds_port
  db_name                     = var.rds_db_name
  username                    = var.rds_master_db_user
  # Password management
  manage_master_user_password = var.rds_manage_master_user_secret
  master_user_secret_kms_key_id = var.rds_manage_master_user_secret ? var.rds_master_user_secret_kms_key_id : null
  deletion_protection         = true
  vpc_security_group_ids      = var.rds_security_group_id
  db_subnet_group_name        = var.rds_db_subnet_group_name
  availability_zone           = var.rds_availability_zone
  multi_az                    = false
  apply_immediately           = true
  backup_window               = var.rds_backup_window
  backup_retention_period     = var.rds_backup_retention_period
  maintenance_window          = var.rds_maintenance_window
  skip_final_snapshot         = true
  final_snapshot_identifier   = "${var.project_name}-final-snapshot-${var.env}"
  copy_tags_to_snapshot       = true
  performance_insights_enabled= false
  monitoring_interval         = 0
  parameter_group_name        = var.rds_parameter_group_name
  tags = merge({
    Project     = var.project_name
    Service     = "${var.project_name}-rds-${var.env}"
    Environment = var.env
    Terraform   = "true"
  }, var.tags)
} 