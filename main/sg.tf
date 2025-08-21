# Centralized Security Groups Configuration
# All security groups for ALB, RDS, Bastion, ECS services, and Redis

##########################################################
# ALB Security Group
##########################################################
module "ecs-alb-sg" {
  source                     = "../modules/security/security-group"
  create_security_group      = var.create_ecs_ecosystem
  security_group_name        = "${var.project_name}-${var.env}-alb-sg"
  security_group_description = "Security group for ECS Application Load Balancer"
  vpc_id                     = module.vpc.vpc_id
  project_name               = var.project_name
  env                        = var.env
  use_cidr_rules             = var.create_ecs_ecosystem
  use_sg_rules               = false
  ingress_rules_cidr         = [
    { from_port = 80, to_port = 80, protocol = "tcp", description = "Allow HTTP from internet", cidr_blocks = "0.0.0.0/0" },
    { from_port = 443, to_port = 443, protocol = "tcp", description = "Allow HTTPS from internet", cidr_blocks = "0.0.0.0/0" }
  ]
  egress_rules_cidr          = [
    { from_port = 0, to_port = 0, protocol = "-1", description = "Allow all outbound IPv4 traffic", cidr_blocks = "0.0.0.0/0" }
  ]
  tags = {
    Name        = "${var.project_name}-${var.env}-alb-sg"
    Project     = var.project_name
    Service     = "alb-security-group"
    Environment = var.env
    Terraform   = "true"
  }
}

##########################################################
# RDS Security Group
##########################################################
module "rds-sg" {
  count  = var.create_rds_database ? 1 : 0
  source = "../modules/security/security-group"
  create_security_group      = var.create_rds_database
  security_group_name        = "${var.project_name}-${var.env}-rds-sg"
  security_group_description = "Security group for RDS database"
  vpc_id                     = module.vpc.vpc_id
  project_name               = var.project_name
  env                        = var.env
  use_cidr_rules             = var.create_rds_database
  use_sg_rules               = false
  ingress_rules_cidr         = [
    { from_port = 5432, to_port = 5432, protocol = "tcp", description = "Allow PostgreSQL from VPC", cidr_blocks = "10.10.0.0/16" }
  ]
  egress_rules_cidr          = [
    { from_port = 0, to_port = 0, protocol = "-1", description = "Allow all outbound IPv4 traffic", cidr_blocks = "0.0.0.0/0" }
  ]
  tags = {
    Name        = "${var.project_name}-${var.env}-rds-sg"
    Project     = var.project_name
    Service     = "rds-security-group"
    Environment = var.env
    Terraform   = "true"
  }
}

##########################################################
# Bastion Security Group
##########################################################
module "ec2-bastion-sg" {
  count  = var.create_bastion && var.create_vpc ? 1 : 0
  source = "../modules/security/security-group"
  create_security_group      = var.create_bastion && var.create_vpc
  security_group_name        = "${var.project_name}-${var.env}-bastion-sg"
  security_group_description = "Security group for Bastion host"
  vpc_id                     = module.vpc.vpc_id
  project_name               = var.project_name
  env                        = var.env
  use_cidr_rules             = var.create_bastion && var.create_vpc
  use_sg_rules               = false
  ingress_rules_cidr         = [
    { from_port = 22, to_port = 22, protocol = "tcp", description = "Allow SSH from internet", cidr_blocks = "0.0.0.0/0" }
  ]
  egress_rules_cidr          = [
    { from_port = 0, to_port = 0, protocol = "-1", description = "Allow all outbound IPv4 traffic", cidr_blocks = "0.0.0.0/0" }
  ]
  tags = {
    Name        = "${var.project_name}-${var.env}-bastion-sg"
    Project     = var.project_name
    Service     = "bastion-security-group"
    Environment = var.env
    Terraform   = "true"
  }
}

##########################################################
# Redis Security Group
##########################################################
module "redis-sg" {
  count  = var.create_elasticache ? 1 : 0
  source = "../modules/security/security-group"
  create_security_group      = var.create_elasticache
  security_group_name        = "${var.project_name}-${var.env}-redis-sg"
  security_group_description = "Security group for ElastiCache Redis"
  vpc_id                     = module.vpc.vpc_id
  project_name               = var.project_name
  env                        = var.env
  use_cidr_rules             = false
  use_sg_rules               = var.create_elasticache
  ingress_rules_sg           = [
    { from_port = 6379, to_port = 6379, protocol = "tcp", description = "Allow Redis from ECS", source_security_group_id = module.ecs-alb-sg.security_group_id }
  ]
  egress_rules_cidr          = [
    { from_port = 0, to_port = 0, protocol = "-1", description = "Allow all outbound IPv4 traffic", cidr_blocks = "0.0.0.0/0" }
  ]
  tags = {
    Name        = "${var.project_name}-${var.env}-redis-sg"
    Project     = var.project_name
    Service     = "redis-security-group"
    Environment = var.env
    Terraform   = "true"
  }
} 