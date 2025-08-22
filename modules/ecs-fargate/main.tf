# ECS Fargate Module - Creates ECS cluster, services, and task definitions

# Auto-generate ECS services from Master Services Configuration
locals {
  services_list = [for k, v in var.services : merge(v, { key = k })]
  
  # Generate ECR repository names for each service
  ecr_repositories = {
    for service in local.services_list : service.container_name => {
      name = "${var.project_name}-${service.container_name}-${var.env}"
    }
  }
}

##########################################################
# ECS Cluster
##########################################################
resource "aws_ecs_cluster" "main" {
  count = var.create_ecs_cluster ? 1 : 0
  name  = "${var.project_name}-cluster-${var.env}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "${var.project_name}-cluster-${var.env}"
    Project     = var.project_name
    Service     = "ecs-cluster"
    Environment = var.env
    Terraform   = "true"
  }
}

##########################################################
# ECS Task Definition
##########################################################
resource "aws_ecs_task_definition" "services" {
  for_each = var.create_ecs_cluster ? var.services : {}

  family                   = "${var.project_name}-${each.value.container_name}-${var.env}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  # Calculate total CPU and memory for valid Fargate combinations
  cpu                      = each.value.cpu + (each.value.enable_xray ? each.value.xray_daemon_cpu : 0) + (each.value.enable_celery_worker ? each.value.celery_worker_cpu : 0)
  memory                   = each.value.memory + (each.value.enable_xray ? each.value.xray_daemon_memory : 0) + (each.value.enable_celery_worker ? each.value.celery_worker_memory : 0)
  
  # Validate Fargate CPU and memory combinations
  # Valid combinations: 0.25vCPU(256)-0.5GB, 0.5vCPU(512)-1GB, 1vCPU(1024)-2GB, 2vCPU(2048)-4GB, 4vCPU(4096)-8GB, etc.
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  # Use a local variable to ensure both containers use the same dynamic tag
  # The image_tag will be updated by CodePipeline, and both containers should use the same tag
  container_definitions = jsonencode(
    concat(
      [
        {
          name  = each.value.container_name
          image = "${var.ecr_repository_urls[each.key]}:${each.value.image_tag}"

          cpu    = each.value.cpu
          memory = each.value.memory
          enable_execute_command = each.value.enable_exec

          portMappings = [
            {
              containerPort = each.value.container_port
              hostPort      = each.value.container_port
              protocol      = "tcp"
            }
          ]

          environment = concat(
            [
              {
                name  = "ENVIRONMENT"
                value = var.env
              },
              {
                name  = "SERVICE_NAME"
                value = each.value.container_name
              }
            ],
            each.value.enable_xray ? [
              {
                name  = "AWS_XRAY_DAEMON_ADDRESS"
                value = "127.0.0.1:2000"
              },
              {
                name  = "AWS_XRAY_CONTEXT_MISSING"
                value = "LOG_ERROR"
              }
            ] : [],
            each.value.environment_variables != null ? each.value.environment_variables : []
          )

          secrets = each.value.secrets != null ? each.value.secrets : []

          logConfiguration = {
            logDriver = "awslogs"
            options = {
              awslogs-group         = aws_cloudwatch_log_group.services[each.key].name
              awslogs-region        = var.region
              awslogs-stream-prefix = "ecs"
            }
          }

          command = length(each.value.command) > 0 ? each.value.command : null

          healthCheck = {
            command     = ["CMD-SHELL", "curl -f http://localhost:${each.value.container_port}${each.value.health_check_path} || exit 1"]
            interval    = 30
            timeout     = 5
            retries     = 3
            startPeriod = 60
          }

          dependsOn = concat(
            each.value.enable_xray ? [
              {
                containerName = "xray-daemon"
                condition     = "START"
              }
            ] : [],
            each.value.enable_celery_worker ? [
              {
                containerName = "celery-worker"
                condition     = "START"
              }
            ] : []
          )
        }
      ],
      [
        {
          name  = "xray-daemon"
          image = "public.ecr.aws/xray/aws-xray-daemon:latest"

          cpu    = each.value.xray_daemon_cpu
          memory = each.value.xray_daemon_memory

          portMappings = [
            {
              containerPort = 2000
              protocol      = "udp"
            }
          ]

          environment = [
            {
              name  = "AWS_REGION"
              value = var.region
            }
          ]

          logConfiguration = {
            logDriver = "awslogs"
            options = {
              awslogs-group         = aws_cloudwatch_log_group.services[each.key].name
              awslogs-region        = var.region
              awslogs-stream-prefix = "xray"
            }
          }

          essential = true
        }
      ],
      each.value.enable_celery_worker ? [
        {
          name  = "celery-worker"
          image = "${var.ecr_repository_urls[each.key]}:${each.value.image_tag}"

          cpu    = each.value.celery_worker_cpu
          memory = each.value.celery_worker_memory

          entrypoint = []
          command = each.value.celery_worker_command

          environment = concat(
            [
              {
                name  = "ENVIRONMENT"
                value = var.env
              },
              {
                name  = "SERVICE_NAME"
                value = "celery-worker"
              },
              {
                name  = "CELERY_WORKER_NAME"
                value = "celery-worker"
              },
              {
                name  = "PYTHONUNBUFFERED"
                value = "1"
              },
              {
                name  = "CELERY_LOG_LEVEL"
                value = "INFO"
              }
            ],
            each.value.environment_variables != null ? each.value.environment_variables : []
          )

          secrets = each.value.secrets != null ? each.value.secrets : []

          logConfiguration = {
            logDriver = "awslogs"
            options = {
              awslogs-group         = aws_cloudwatch_log_group.services[each.key].name
              awslogs-region        = var.region
              awslogs-stream-prefix = "celery-worker"
              awslogs-create-group  = "true"
              awslogs-datetime-format = "%Y-%m-%d %H:%M:%S"
            }
          }

          essential = true
        }
      ] : []
    )
  )

  tags = merge({
    Name        = "${var.project_name}-${each.value.container_name}-task-${var.env}"
    Project     = var.project_name
    Service     = "${var.project_name}-${each.value.container_name}-task-${var.env}"
    Environment = var.env
    Component   = "ecs-task-definition"
    Container   = each.value.container_name
    LaunchType  = "FARGATE"
    Terraform   = "true"
  }, var.tags)
}

##########################################################
# ECS Services
##########################################################
resource "aws_ecs_service" "services" {
  for_each = var.create_ecs_cluster ? var.services : {}

  name            = "${var.project_name}-${each.value.container_name}-${var.env}"
  cluster         = aws_ecs_cluster.main[0].id
  task_definition = aws_ecs_task_definition.services[each.key].arn
  desired_count   = each.value.desired_count
  launch_type     = "FARGATE"
  enable_execute_command = each.value.enable_exec

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_services[each.key].id]
    assign_public_ip = false
  }

      load_balancer {
      target_group_arn = var.alb_target_group_arns[each.key]
      container_name   = each.value.container_name
      container_port   = each.value.container_port
    }

  tags = {
    Name        = "${var.project_name}-${each.value.container_name}-service-${var.env}"
    Project     = var.project_name
    Service     = "${var.project_name}-${each.value.container_name}-service-${var.env}"
    Environment = var.env
    Terraform   = "true"
  }
}

##########################################################
# CloudWatch Log Groups
##########################################################
resource "aws_cloudwatch_log_group" "services" {
  for_each = var.create_ecs_cluster ? var.services : {}

  name              = "/ecs/${var.project_name}-${each.value.container_name}-${var.env}"
  retention_in_days = 30

  tags = {
    Name        = "${var.project_name}-${each.value.container_name}-logs-${var.env}"
    Project     = var.project_name
    Service     = "${var.project_name}-${each.value.container_name}-log-group-${var.env}"
    Environment = var.env
    Terraform   = "true"
  }
}

##########################################################
# Security Groups
##########################################################
resource "aws_security_group" "ecs_services" {
  for_each = var.create_ecs_cluster ? var.services : {}

  name        = "${var.project_name}-${each.value.container_name}-sg-${var.env}"
  description = "Security group for ECS service ${each.value.container_name}"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = each.value.container_port
    to_port         = each.value.container_port
    protocol        = "tcp"
    security_groups = [var.alb_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${each.value.container_name}-sg-${var.env}"
    Project     = var.project_name
    Service     = "${var.project_name}-${each.value.container_name}-security-group-${var.env}"
    Environment = var.env
    Terraform   = "true"
  }
}

##########################################################
# Auto Scaling
##########################################################
resource "aws_appautoscaling_target" "ecs_target" {
  for_each = var.create_ecs_cluster ? var.services : {}

  max_capacity       = each.value.max_capacity
  min_capacity       = each.value.min_capacity
  resource_id        = "service/${aws_ecs_cluster.main[0].name}/${aws_ecs_service.services[each.key].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# CPU-based auto scaling
resource "aws_appautoscaling_policy" "ecs_cpu_policy" {
  for_each = var.create_ecs_cluster ? var.services : {}

  name               = "${var.project_name}-${each.value.container_name}-cpu-autoscaling-${var.env}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = each.value.target_cpu_utilization
  }
}

# Memory-based auto scaling
resource "aws_appautoscaling_policy" "ecs_memory_policy" {
  for_each = var.create_ecs_cluster ? var.services : {}

  name               = "${var.project_name}-${each.value.container_name}-memory-autoscaling-${var.env}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = each.value.target_memory_utilization
  }
} 