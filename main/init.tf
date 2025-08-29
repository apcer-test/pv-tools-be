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