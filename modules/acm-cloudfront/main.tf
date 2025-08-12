# ACM Certificate Module for CloudFront
# Creates SSL certificates for CloudFront (must be in us-east-1)

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0.0"
      configuration_aliases = [aws.us_east_1]
    }
  }
}

# ACM Certificate for CloudFront (must be in us-east-1)
resource "aws_acm_certificate" "cloudfront" {
  count = var.create_certificate ? 1 : 0

  provider = aws.us_east_1  # CloudFront requires certificates in us-east-1

  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = var.subject_alternative_names

  lifecycle {
    create_before_destroy = true
  }

  tags = merge({
    Name        = "${var.project_name}-${var.env}-cloudfront-cert"
    Project     = var.project_name
    Service     = "acm-certificate"
    Environment = var.env
    Terraform   = "true"
  }, var.tags)
}

# DNS validation records for CloudFront certificate
resource "aws_route53_record" "cloudfront_validation" {
  for_each = var.create_certificate ? {
    for dvo in aws_acm_certificate.cloudfront[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  provider = aws  # Use default provider for Route53

  zone_id = var.route53_zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60
}

# Certificate validation for CloudFront
resource "aws_acm_certificate_validation" "cloudfront" {
  count = var.create_certificate ? 1 : 0

  provider = aws.us_east_1

  certificate_arn         = aws_acm_certificate.cloudfront[0].arn
  validation_record_fqdns = [for record in aws_route53_record.cloudfront_validation : record.fqdn]

  timeouts {
    create = "5m"
  }
} 