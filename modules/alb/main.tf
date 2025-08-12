# Application Load Balancer Module - Flexible Services Configuration

# Auto-generate ALB services from Master Services Configuration
locals {
  services_list = [for k, v in var.services : merge(v, { key = k })]
  
  alb_services = {
    for idx, service in local.services_list : "${service.container_name}-${var.env}" => {
      name               = "${service.container_name}-${var.env}"
      port               = service.container_port
      protocol           = "HTTP"
      target_type        = "ip"
      health_check_path  = service.health_check_path
      health_check_port  = "traffic-port"
      domain             = service.domain
      priority           = (idx + 1) * 100  # Generate priority: 100, 200, 300, etc.
    }
  }
}

##########################################################
# Application Load Balancer
##########################################################
resource "aws_lb" "alb" {
  count              = var.create_alb ? 1 : 0
  name               = var.alb_name
  internal           = var.alb_internal
  load_balancer_type = "application"
  security_groups    = var.alb_security_groups
  subnets            = var.alb_public_subnet_ids

  enable_deletion_protection = var.alb_enable_deletion_protection

  tags = merge(
    {
      Name        = var.alb_name
      Project     = var.project_name
      Service     = "load-balancer"
      Environment = var.env
      Terraform   = "true"
    }
  )
}

##########################################################
# Target Groups (dynamic based on services)
##########################################################
resource "aws_lb_target_group" "services" {
  for_each = var.create_alb ? local.alb_services : {}
  name        = each.value.name
  port        = each.value.port
  protocol    = "HTTP"
  vpc_id      = var.alb_vpc_id
  target_type = "ip"

  health_check {
    path                = each.value.health_check_path
    protocol            = "HTTP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(
    {
      Name        = each.value.name
      Project     = var.project_name
      Service     = "${each.value.name}-target-group"
      Environment = var.env
      Terraform   = "true"
    }
  )
}

##########################################################
# ALB Listener on HTTP (port 80)
##########################################################
resource "aws_lb_listener" "http_listener" {
  count             = var.create_alb ? 1 : 0
  load_balancer_arn = aws_lb.alb[0].arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "404: Not Found"
      status_code  = "404"
    }
  }

  tags = merge(
    {
      Name        = "${var.alb_name}-http-listener"
      Project     = var.project_name
      Service     = "load-balancer-listener"
      Environment = var.env
      Terraform   = "true"
    }
  )
}

##########################################################
# ALB Listener Rules (dynamic based on services)
##########################################################
resource "aws_lb_listener_rule" "services" {
  for_each = var.create_alb ? local.alb_services : {}

  listener_arn = aws_lb_listener.http_listener[0].arn
  priority     = each.value.priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.services[each.key].arn
  }

  condition {
    host_header {
      values = [each.value.domain]
    }
  }

  tags = merge(
    {
      Name        = "${each.value.name}-rule"
      Project     = var.project_name
      Service     = "${each.value.name}-listener-rule"
      Environment = var.env
      Terraform   = "true"
    }
  )
} 