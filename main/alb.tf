# Application Load Balancer Configuration
# Creates ALB with auto-generated target groups and listeners from services

module "ecs-alb" {
  source                      = "../modules/alb"
  create_alb                  = var.create_ecs_ecosystem
  alb_name                    = "${var.project_name}-${var.env}-alb"
  alb_internal                = false
  alb_security_groups         = [module.ecs-alb-sg.security_group_id]
  alb_public_subnet_ids       = module.vpc.public_subnet_ids
  alb_vpc_id                  = module.vpc.vpc_id
  alb_enable_deletion_protection = var.alb_enable_deletion_protection
  
  # Simple services input - module handles all ALB resource generation
  services = var.services
  
  project_name = var.project_name
  env          = var.env
}
