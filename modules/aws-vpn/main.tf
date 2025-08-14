# AWS VPN Module
# Supports both Client VPN and Site-to-Site VPN

# Client VPN Endpoint
resource "aws_ec2_client_vpn_endpoint" "main" {
  count = var.create_client_vpn ? 1 : 0

  description            = "${var.project_name}-${var.env}-client-vpn"
  server_certificate_arn = aws_acm_certificate.client_vpn_server[0].arn
  client_cidr_block     = var.client_vpn_cidr_block

  authentication_options {
    type                       = "certificate-authentication"
    root_certificate_chain_arn = aws_acm_certificate.client_vpn_server[0].arn
  }

  connection_log_options {
    enabled = false
  }

  split_tunnel = var.split_tunnel
  vpc_id       = var.vpc_id

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.env}-client-vpn"
    Project     = var.project_name
    Service     = "client-vpn"
    Environment = var.env
    Terraform   = "true"
  })
}

# Client VPN Network Association
resource "aws_ec2_client_vpn_network_association" "main" {
  for_each = var.create_client_vpn ? toset(var.client_vpn_subnet_ids) : []

  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.main[0].id
  subnet_id              = each.value
}

# Client VPN Authorization Rule
resource "aws_ec2_client_vpn_authorization_rule" "main" {
  for_each = var.create_client_vpn ? toset(var.client_vpn_authorized_networks) : []

  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.main[0].id
  target_network_cidr    = each.value
  authorize_all_groups   = true
}

# Site-to-Site VPN Gateway
resource "aws_vpn_gateway" "main" {
  count = var.create_site_to_site_vpn ? 1 : 0

  vpc_id = var.vpc_id

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.env}-vpn-gateway"
    Project     = var.project_name
    Service     = "vpn-gateway"
    Environment = var.env
    Terraform   = "true"
  })
}

# Customer Gateway
resource "aws_customer_gateway" "main" {
  for_each = var.create_site_to_site_vpn ? var.customer_gateways : {}

  bgp_asn    = each.value.bgp_asn
  ip_address = each.value.ip_address
  type       = "ipsec.1"

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.env}-cgw-${each.key}"
    Project     = var.project_name
    Service     = "customer-gateway"
    Environment = var.env
    Terraform   = "true"
  })
}

# VPN Connection
resource "aws_vpn_connection" "main" {
  for_each = var.create_site_to_site_vpn ? var.customer_gateways : {}

  vpn_gateway_id      = aws_vpn_gateway.main[0].id
  customer_gateway_id = aws_customer_gateway.main[each.key].id
  type                = "ipsec.1"

  static_routes_only = each.value.static_routes_only

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.env}-vpn-${each.key}"
    Project     = var.project_name
    Service     = "vpn-connection"
    Environment = var.env
    Terraform   = "true"
  })
}

# VPN Connection Route
resource "aws_vpn_connection_route" "main" {
  for_each = var.create_site_to_site_vpn ? {
    for route in local.vpn_routes : "${route.vpn_key}-${route.cidr}" => route
  } : {}

  destination_cidr_block = each.value.cidr
  vpn_connection_id      = aws_vpn_connection.main[each.value.vpn_key].id
}

# ACM Certificate for Client VPN Server
resource "aws_acm_certificate" "client_vpn_server" {
  count = var.create_client_vpn ? 1 : 0

  domain_name       = "server.${var.client_vpn_domain}"
  validation_method = "DNS"

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.env}-client-vpn-server-cert"
    Project     = var.project_name
    Service     = "acm"
    Environment = var.env
    Terraform   = "true"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# ACM Certificate for Client VPN Client
resource "aws_acm_certificate" "client_vpn_client" {
  count = var.create_client_vpn ? 1 : 0

  domain_name       = "client.${var.client_vpn_domain}"
  validation_method = "DNS"

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.env}-client-vpn-client-cert"
    Project     = var.project_name
    Service     = "acm"
    Environment = var.env
    Terraform   = "true"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# CloudWatch Log Group for Client VPN Logs
resource "aws_cloudwatch_log_group" "client_vpn_logs" {
  count = var.create_client_vpn && var.enable_connection_logging ? 1 : 0

  name              = "/aws/client-vpn/${var.project_name}-${var.env}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.env}-client-vpn-logs"
    Project     = var.project_name
    Service     = "cloudwatch-logs"
    Environment = var.env
    Terraform   = "true"
  })
}

# Local values for VPN routes
locals {
  vpn_routes = var.create_site_to_site_vpn ? flatten([
    for vpn_key, vpn_config in var.customer_gateways : [
      for cidr in vpn_config.static_routes : {
        vpn_key = vpn_key
        cidr    = cidr
      }
    ]
  ]) : []
} 