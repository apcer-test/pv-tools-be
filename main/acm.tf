# ACM Certificate Configuration
# Creates SSL certificates for CloudFront and ALB

# ACM Module for CloudFront certificates (requires us-east-1)
module "acm_cloudfront" {
  count  = var.create_acm_certificates ? 1 : 0
  source = "../modules/acm-cloudfront"

  create_certificate = true
  domain_name       = var.domain_name
  subject_alternative_names = var.certificate_subject_alternative_names
  route53_zone_id   = var.route53_zone_id
  project_name      = var.project_name
  env               = var.env
  tags = {
    Name        = "${var.project_name}-${var.env}-cloudfront-cert"
    Project     = var.project_name
    Service     = "acm-cloudfront"
    Environment = var.env
    Terraform   = "true"
  }

  providers = {
    aws.us_east_1 = aws.us_east_1
  }
}

# ACM Module for regional certificates (ALB) - uses default provider
module "acm_regional" {
  count  = var.create_acm_certificates ? 1 : 0
  source = "../modules/acm"

  create_regional_certificate = true
  domain_name                 = var.domain_name
  subject_alternative_names   = var.certificate_subject_alternative_names
  route53_zone_id            = var.route53_zone_id
  project_name               = var.project_name
  env                        = var.env
  tags = {
    Name        = "${var.project_name}-${var.env}-regional-cert"
    Project     = var.project_name
    Service     = "acm-regional"
    Environment = var.env
    Terraform   = "true"
  }
} 