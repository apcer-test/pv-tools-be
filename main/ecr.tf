locals {
  ecr_repositories = [
    for service_key, service in var.services : {
      name            = "${var.project_name}-${service.container_name}-${var.env}"
      retention_count = var.env == "prod" ? 7 : 4  # Prod: 7 days, Dev: 4 days
      force_delete    = true
      scan_on_push    = true
    }
  ]
}

# ECR Repositories (Auto-created when ECS is enabled - stores container images)
module "ecs-ecr" {
  source                  = "../modules/ecr"
  create_ecr_repositories = var.create_ecs_ecosystem  # Auto-enabled when ECS ecosystem is created
  project_name            = var.project_name
  env                     = var.env
  ecr_repositories        = local.ecr_repositories
} 