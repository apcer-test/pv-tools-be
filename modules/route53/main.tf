# Route53 Module - DNS Management

# Local to determine which zone ID to use
locals {
  zone_id = var.create_hosted_zone ? aws_route53_zone.main[0].zone_id : var.zone_id
}

# Hosted Zone
resource "aws_route53_zone" "main" {
  count = var.create_hosted_zone ? 1 : 0
  
  name = var.domain_name
  
  tags = {
    Name        = "${var.project_name}-hosted-zone-${var.env}"
    Project     = var.project_name
    Service     = "route53-hosted-zone"
    Environment = var.env
    Terraform   = "true"
  }
}

# A Records
resource "aws_route53_record" "a_records" {
  for_each = var.a_records

  zone_id = local.zone_id
  name    = each.value.name
  type    = "A"
  ttl     = each.value.ttl

  records = each.value.records
}

# CNAME Records
resource "aws_route53_record" "cname_records" {
  for_each = var.cname_records

  zone_id = local.zone_id
  name    = each.value.name
  type    = "CNAME"
  ttl     = each.value.ttl

  records = [each.value.record]
}

# MX Records
resource "aws_route53_record" "mx_records" {
  for_each = var.mx_records

  zone_id = local.zone_id
  name    = each.value.name
  type    = "MX"
  ttl     = each.value.ttl

  records = each.value.records
}

# TXT Records
resource "aws_route53_record" "txt_records" {
  for_each = var.txt_records

  zone_id = local.zone_id
  name    = each.value.name
  type    = "TXT"
  ttl     = each.value.ttl

  records = each.value.records
}

# Alias Records
resource "aws_route53_record" "alias_records" {
  for_each = var.alias_records

  zone_id = local.zone_id
  name    = each.value.name
  type    = each.value.type

  alias {
    name                   = each.value.alias_name
    zone_id                = each.value.alias_zone_id
    evaluate_target_health = each.value.evaluate_target_health
  }
}

# Health Checks
resource "aws_route53_health_check" "main" {
  for_each = var.health_checks

  fqdn              = each.value.fqdn
  port              = each.value.port
  type              = each.value.type
  resource_path     = each.value.resource_path
  failure_threshold = each.value.failure_threshold
  request_interval  = each.value.request_interval

  tags = {
    Name        = "${var.project_name}-health-check-${each.key}-${var.env}"
    Project     = var.project_name
    Service     = "route53-health-check"
    Environment = var.env
    Terraform   = "true"
  }
}

# Failover Records
resource "aws_route53_record" "failover_records" {
  for_each = var.failover_records

  zone_id = local.zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = each.value.ttl

  set_identifier = each.value.set_identifier
  health_check_id = each.value.health_check_id
  failover_routing_policy {
    type = each.value.failover_type
  }

  records = each.value.records
} 