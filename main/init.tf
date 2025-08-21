# Terraform and provider versions

terraform {
  required_version = ">= 1.9.0"
  
  # Partial backend configuration - completed at init time with -backend-config
  backend "s3" {
    # Backend details provided via -backend-config flag during terraform init
    # This allows different S3 buckets for different clients
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.4.0"
    }
  }
}

# AWS Provider configuration
provider "aws" {
  region  = var.region
}

# AWS Provider for us-east-1 (required for CloudFront certificates)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

# ACM Certificate Module
module "acm" {
  count = var.create_acm_certificate ? 1 : 0
  source = "../modules/acm"
  providers = { aws = aws.us_east_1 }
  
  create_regional_certificate = true
  domain_name = var.acm_domain_name
  subject_alternative_names = var.acm_subject_alternative_names
  route53_zone_id = var.route53_zone_id
  
  project_name = var.project_name
  env = var.env
  tags = local.common_tags
}

# Output CNAME records for DNS validation
output "acm_validation_records" {
  description = "CNAME records to add to DNS for ACM certificate validation"
  value = var.create_acm_certificate ? {
    for dvo in module.acm[0].validation_records : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}
}

output "cloudfront_distribution_domain" {
  description = "CloudFront distribution domain name"
  value = try(module.cloudfront_s3["frontend-cloudfront"].cloudfront_domain_name, "")
}

output "cloudfront_distribution_aliases" {
  description = "CloudFront distribution aliases (CNAME records to add to DNS)"
  value = try(module.cloudfront_s3["frontend-cloudfront"].cloudfront_aliases, [])
}