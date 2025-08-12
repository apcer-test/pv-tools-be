variable "allocated_storage" {
  description = "The allocated storage in gigabytes."
  type        = number
}

variable "engine" {
  description = "The database engine to use (e.g., mysql, postgres)."
  type        = string
}

variable "engine_version" {
  description = "The version of the database engine."
  type        = string
}

variable "instance_class" {
  description = "The instance type of the RDS instance."
  type        = string
}

variable "db_name" {
  description = "The name of the database to create."
  type        = string
}

variable "username" {
  description = "Username for the master DB user."
  type        = string
}


# variable "password" {
#   description = "Password for the master DB user."
#   type        = string
#   sensitive   = true
# }

variable "db_subnet_group_name" {
  description = "Name of DB subnet group."
  type        = string
}

variable "vpc_security_group_ids" {
  description = "List of VPC security groups to associate."
  type        = list(string)
}

variable "multi_az" {
  description = "Specifies if the RDS instance is multi-AZ."
  type        = bool
  default     = false
}

variable "storage_encrypted" {
  description = "Specifies whether the DB instance is encrypted."
  type        = bool
  default     = true
}

variable "backup_retention_period" {
  description = "The days to retain backups for."
  type        = number
  default     = 7
}

variable "skip_final_snapshot" {
  description = "Whether to skip taking a final DB snapshot before deletion."
  type        = bool
  default     = false
}

variable "final_snapshot_identifier" {
  description = "The name of your final DB snapshot when this DB instance is deleted."
  type        = string
  default     = null
}

variable "performance_insights_enabled" {
  description = "Specifies whether Performance Insights are enabled."
  type        = bool
  default     = false
}

variable "performance_insights_retention_period" {
  description = "Amount of time in days to retain Performance Insights data."
  type        = number
  default     = 7
}

variable "snapshot_identifier" {
  description = "Specifies whether or not to create this database from a snapshot."
  type        = string
  default     = null
}

variable "project_name" {
  description = "The name of the project."
  type        = string
}

variable "env" {
  description = "The environment (e.g., dev, prod)."
  type        = string
}

variable "tags" {
  description = "A map of tags to assign to the resource."
  type        = map(string)
  default     = {}
}

variable "rds_instance_name" {
  description = "The name of the RDS instance."
  type        = string
}

variable "rds_instance_class" {
  description = "The instance type of the RDS instance."
  type        = string
}

variable "rds_allocated_storage" {
  description = "The allocated storage in gigabytes."
  type        = number
}

variable "rds_max_allocated_storage" {
  description = "The maximum allocated storage for autoscaling."
  type        = number
  default     = null
}

variable "rds_storage_type" {
  description = "The storage type to use (e.g., gp2, gp3, io1)."
  type        = string
  default     = "gp2"
}

variable "rds_engine" {
  description = "The database engine to use (e.g., mysql, postgres)."
  type        = string
}

variable "rds_engine_version" {
  description = "The version of the database engine."
  type        = string
}

variable "rds_port" {
  description = "The port on which the DB accepts connections."
  type        = number
  default     = 3306
}

variable "rds_db_name" {
  description = "The name of the database to create."
  type        = string
}

variable "rds_master_db_user" {
  description = "Username for the master DB user."
  type        = string
}

variable "rds_security_group_id" {
  description = "List of VPC security groups to associate."
  type        = list(string)
}

variable "rds_db_subnet_group_name" {
  description = "Name of DB subnet group."
  type        = string
}

variable "rds_availability_zone" {
  description = "The AZ for the DB instance."
  type        = string
  default     = null
}

variable "rds_backup_window" {
  description = "Preferred backup window."
  type        = string
  default     = null
}

variable "rds_backup_retention_period" {
  description = "The days to retain backups for."
  type        = number
  default     = 7
}

variable "rds_maintenance_window" {
  description = "Preferred maintenance window."
  type        = string
  default     = null
}

variable "rds_parameter_group_name" {
  description = "Name of the DB parameter group."
  type        = string
  default     = null
}

variable "parameters" {
  description = "A map of DB parameter group parameters."
  type        = any
  default     = {}
}

variable "enable_instance_scheduler" {
  description = "Enable instance scheduler tag."
  type        = bool
  default     = false
}

variable "name" {
  description = "Project name for tagging."
  type        = string
}

variable "app" {
  description = "Service/app name for tagging."
  type        = string
}

variable "rds_master_db_password" {
  description = "Password for the master DB user (optional when manage_master_user_password = true)."
  type        = string
  sensitive   = true
  default     = null
} 