# Security Configuration
# Creates AWS Config, GuardDuty, WAF, Inspector, and Security Hub

# Security Module
module "security" {
  count  = var.create_security ? 1 : 0
  source = "../modules/security"

  create_aws_config = true
  create_guardduty  = true
  create_waf        = true
  create_inspector  = true
  create_security_hub = true
  enable_finding_aggregator = false   # if true, then finding_aggregator_excluded_regions is required coz this support multiple regions and account
  finding_aggregator_excluded_regions = []
  
  project_name = var.project_name
  env          = var.env
  region       = var.region
  
  blocked_ip_addresses = var.blocked_ip_addresses
  known_ip_addresses   = var.known_ip_addresses
  
  tags = {
    Name        = "${var.project_name}-${var.env}-security"
    Project     = var.project_name
    Service     = "security"
    Environment = var.env
    Terraform   = "true"
  }

  providers = {
    aws.us_east_1 = aws.us_east_1
  }
} 