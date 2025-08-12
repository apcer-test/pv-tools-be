# CloudWatch Synthetics Configuration
# Creates synthetic monitoring canaries for endpoint health checks

# CloudWatch Synthetics Module
module "synthetics" {
  count  = var.create_synthetics ? 1 : 0
  source = "../modules/cloudwatch-synthetics"

  create_synthetics = true
  project_name      = var.project_name
  env               = var.env
  artifacts_bucket_arn = ""  # Will be auto-created by the module

  # Canary configurations for monitoring endpoints
  canaries = {
    api_health_check = {
      name                = "${var.project_name}-${var.env}-api-health"
      runtime_version     = "syn-nodejs-puppeteer-6.2"
      start_canary        = true
      schedule_expression = var.synthetics.api_health_check.schedule
      timeout_in_seconds  = var.synthetics.api_health_check.timeout
      memory_in_mb        = var.synthetics.api_health_check.memory_size
      active_tracing      = true
      subnet_ids          = module.vpc.private_subnet_ids
      security_group_ids  = [module.ecs-alb-sg.security_group_id]
      target_url          = var.synthetics.api_health_check.target_url
    }
    admin_health_check = {
      name                = "${var.project_name}-${var.env}-admin-health"
      runtime_version     = "syn-nodejs-puppeteer-6.2"
      start_canary        = true
      schedule_expression = var.synthetics.admin_health_check.schedule
      timeout_in_seconds  = var.synthetics.admin_health_check.timeout
      memory_in_mb        = var.synthetics.admin_health_check.memory_size
      active_tracing      = true
      subnet_ids          = module.vpc.private_subnet_ids
      security_group_ids  = [module.ecs-alb-sg.security_group_id]
      target_url          = var.synthetics.admin_health_check.target_url
    }
  }

  # Alarm actions (SNS topics, etc.)
  alarm_actions = []

  tags = {
    Name        = "${var.project_name}-${var.env}-synthetics"
    Project     = var.project_name
    Service     = "synthetics"
    Environment = var.env
    Terraform   = "true"
  }
} 