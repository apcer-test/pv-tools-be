# ECS Fargate Ecosystem Configuration
# ECS-specific resources only - ALB and CloudFront are in separate files

# IAM Roles for ECS
resource "aws_iam_role" "ecs_execution_role" {
  count = var.create_ecs_ecosystem ? 1 : 0
  name  = "${var.project_name}-ecs-execution-role-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-ecs-execution-role-${var.env}"
    Project     = var.project_name
    Service     = "ecs-execution-role"
    Environment = var.env
    Terraform   = "true"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  count      = var.create_ecs_ecosystem ? 1 : 0
  role       = aws_iam_role.ecs_execution_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task_role" {
  count = var.create_ecs_ecosystem ? 1 : 0
  name  = "${var.project_name}-ecs-task-role-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-ecs-task-role-${var.env}"
    Project     = var.project_name
    Service     = "ecs-task-role"
    Environment = var.env
    Terraform   = "true"
  }
}

# X-Ray permissions for ECS task role
resource "aws_iam_role_policy" "ecs_task_role_xray_policy" {
  count = var.create_ecs_ecosystem ? 1 : 0
  name  = "${var.project_name}-ecs-task-role-xray-policy-${var.env}"
  role  = aws_iam_role.ecs_task_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets",
          "xray:GetSamplingStatisticSummaries"
        ]
        Resource = "*"
      }
    ]
  })
}

# ECS Fargate Cluster and Services

# Create mapping from service keys to ECR repository URLs
locals {
  ecr_repository_urls_map = var.create_ecs_ecosystem ? {
    for service_key, service in var.services : service_key => module.ecs-ecr.repository_urls_map["${var.project_name}-${service.container_name}-${var.env}"]
  } : {}
  
  # Create mapping from service keys to ALB target group ARNs
  alb_target_group_arns_map = var.create_ecs_ecosystem ? {
    for service_key, service in var.services : service_key => module.ecs-alb.target_group_arns["${service.container_name}-${var.env}"]
  } : {}
}

# ECS Fargate Cluster and Services
module "ecs_fargate" {
  count  = var.create_ecs_ecosystem ? 1 : 0
  source = "../modules/ecs-fargate"

  create_ecs_cluster = true
  project_name       = var.project_name
  env                = var.env
  region             = var.region
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  alb_security_group_id = module.ecs-alb-sg.security_group_id
  alb_target_group_arns = local.alb_target_group_arns_map
  ecs_execution_role_arn = aws_iam_role.ecs_execution_role[0].arn
  ecs_task_role_arn     = aws_iam_role.ecs_task_role[0].arn
  ecr_repository_urls   = local.ecr_repository_urls_map
  services           = var.services
} 