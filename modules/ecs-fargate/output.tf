# ECS Fargate Module Outputs

# ECS Cluster outputs
output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main[0].id
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main[0].arn
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main[0].name
}

# ECS Services outputs
output "ecs_service_names" {
  description = "Map of ECS service names"
  value = {
    for k, v in aws_ecs_service.services : k => v.name
  }
}

output "ecs_service_arns" {
  description = "Map of ECS service ARNs"
  value = {
    for k, v in aws_ecs_service.services : k => v.id
  }
}

# Task Definition outputs
output "task_definition_arns" {
  description = "Map of task definition ARNs"
  value = {
    for k, v in aws_ecs_task_definition.services : k => v.arn
  }
}

output "task_definition_families" {
  description = "Map of task definition family names"
  value = {
    for k, v in aws_ecs_task_definition.services : k => v.family
  }
}

# CloudWatch Log Group outputs
output "cloudwatch_log_group_names" {
  description = "Map of CloudWatch log group names"
  value = {
    for k, v in aws_cloudwatch_log_group.services : k => v.name
  }
}

output "cloudwatch_log_group_arns" {
  description = "Map of CloudWatch log group ARNs"
  value = {
    for k, v in aws_cloudwatch_log_group.services : k => v.arn
  }
}

# Security Group outputs
output "security_group_ids" {
  description = "Map of security group IDs for ECS services"
  value = {
    for k, v in aws_security_group.ecs_services : k => v.id
  }
}

output "security_group_arns" {
  description = "Map of security group ARNs for ECS services"
  value = {
    for k, v in aws_security_group.ecs_services : k => v.arn
  }
}

# Auto Scaling outputs
output "autoscaling_target_ids" {
  description = "Map of auto scaling target IDs"
  value = {
    for k, v in aws_appautoscaling_target.ecs_target : k => v.id
  }
}

output "autoscaling_policy_arns" {
  description = "Map of auto scaling policy ARNs"
  value = {
    for k, v in aws_appautoscaling_policy.ecs_cpu_policy : k => v.arn
  }
} 

# Service Discovery outputs
output "service_discovery_service_names" {
  description = "Map of service discovery service names"
  value = var.enable_service_discovery ? {
    for k, v in aws_service_discovery_service.services : k => v.name
  } : {}
}

output "service_discovery_service_arns" {
  description = "Map of service discovery service ARNs"
  value = var.enable_service_discovery ? {
    for k, v in aws_service_discovery_service.services : k => v.arn
  } : {}
}

output "service_discovery_service_ids" {
  description = "Map of service discovery service IDs"
  value = var.enable_service_discovery ? {
    for k, v in aws_service_discovery_service.services : k => v.id
  } : {}
}