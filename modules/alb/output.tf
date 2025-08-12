# ALB Module Outputs - Flexible Services Configuration

##########################################################
# ALB Outputs
##########################################################
output "alb_id" {
  description = "ID of the Application Load Balancer"
  value       = var.create_alb ? aws_lb.alb[0].id : null
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = var.create_alb ? aws_lb.alb[0].arn : null
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = var.create_alb ? aws_lb.alb[0].dns_name : null
}

output "alb_zone_id" {
  description = "Hosted zone ID of the Application Load Balancer"
  value       = var.create_alb ? aws_lb.alb[0].zone_id : null
}

##########################################################
# Target Group Outputs (Dynamic)
##########################################################
output "target_group_arns" {
  description = "Map of service names to target group ARNs"
  value       = var.create_alb ? { for k, v in aws_lb_target_group.services : k => v.arn } : {}
}

output "target_group_names" {
  description = "Map of service names to target group names"
  value       = var.create_alb ? { for k, v in aws_lb_target_group.services : k => v.name } : {}
}

output "target_group_ports" {
  description = "Map of service names to target group ports"
  value       = var.create_alb ? { for k, v in aws_lb_target_group.services : k => v.port } : {}
}

##########################################################
# Listener Outputs
##########################################################
output "http_listener_arn" {
  description = "ARN of the HTTP listener"
  value       = var.create_alb ? aws_lb_listener.http_listener[0].arn : null
}

##########################################################
# Service-Specific Target Group ARNs (for easy ECS integration)
##########################################################
output "target_group_arns_by_service" {
  description = "Target group ARNs by service name (for ECS service configuration)"
  value       = var.create_alb ? { for k, v in aws_lb_target_group.services : k => v.arn } : {}
}

##########################################################
# Complete Services Information
##########################################################
output "services_info" {
  description = "Map of services information including target groups, ARNs, and configurations"
  value = var.create_alb ? {
    for k, v in aws_lb_target_group.services : k => {
      name              = k
      target_group_name = v.name
      target_group_arn  = v.arn
      port              = v.port
      domain            = local.alb_services[k].domain
      health_check_path = local.alb_services[k].health_check_path
      priority          = local.alb_services[k].priority
    }
  } : {}
}

##########################################################
# ALB Endpoint Information
##########################################################
output "alb_endpoint" {
  description = "ALB HTTP endpoint URL"
  value       = var.create_alb ? "http://${aws_lb.alb[0].dns_name}" : null
}

output "route53_alias_config" {
  description = "Configuration for Route53 alias records"
  value = var.create_alb ? {
    name                   = aws_lb.alb[0].dns_name
    zone_id               = aws_lb.alb[0].zone_id
    evaluate_target_health = true
  } : null
} 