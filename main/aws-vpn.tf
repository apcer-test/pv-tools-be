# AWS VPN Configuration
# Supports both Client VPN and Site-to-Site VPN

module "aws_vpn" {
  count  = var.create_aws_vpn ? 1 : 0
  source = "../modules/aws-vpn"

  # VPN Configuration
  create_client_vpn = var.aws_vpn.create_client_vpn
  create_site_to_site_vpn = var.aws_vpn.create_site_to_site_vpn

  # Project Configuration
  project_name = var.project_name
  env          = var.env
  vpc_id       = module.vpc[0].vpc_id

  # Client VPN Configuration
  client_vpn_cidr_block = var.aws_vpn.client_vpn_cidr_block
  client_vpn_subnet_ids = var.aws_vpn.client_vpn_subnet_ids
  client_vpn_authorized_networks = var.aws_vpn.client_vpn_authorized_networks
  client_vpn_domain = var.aws_vpn.client_vpn_domain
  split_tunnel = var.aws_vpn.split_tunnel
  enable_connection_logging = var.aws_vpn.enable_connection_logging
  log_retention_days = var.aws_vpn.log_retention_days

  # Site-to-Site VPN Configuration
  customer_gateways = var.aws_vpn.customer_gateways

  # Tags
  tags = {
    Name        = "${var.project_name}-${var.env}-vpn"
    Project     = var.project_name
    Service     = "aws-vpn"
    Environment = var.env
    Terraform   = "true"
  }
} 