# ACM Certificate Module for Regional Certificates
# Creates SSL certificates for ALB (regional)

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0.0"
    }
  }
}

# ACM Certificate for ALB (regional)
resource "aws_acm_certificate" "regional" {
  count = var.create_regional_certificate ? 1 : 0

  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = var.subject_alternative_names

  lifecycle {
    create_before_destroy = true
  }

  tags = merge({
    Name        = "${var.project_name}-${var.env}-regional-cert"
    Project     = var.project_name
    Service     = "acm-certificate"
    Environment = var.env
    Terraform   = "true"
  }, var.tags)
}

# DNS validation records for regional certificate
resource "aws_route53_record" "regional_validation" {
  for_each = var.create_regional_certificate && var.route53_zone_id != "" ? {
    for dvo in aws_acm_certificate.regional[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  zone_id = var.route53_zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60
}

# Certificate validation for regional (only when Route53 zone is provided)
resource "aws_acm_certificate_validation" "regional" {
  count = var.create_regional_certificate && var.route53_zone_id != "" ? 1 : 0

  certificate_arn         = aws_acm_certificate.regional[0].arn
  validation_record_fqdns = [for record in aws_route53_record.regional_validation : record.fqdn]

  timeouts {
    create = "5m"
  }
} 