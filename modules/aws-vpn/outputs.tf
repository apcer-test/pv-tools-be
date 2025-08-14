# AWS VPN Module Outputs

# Client VPN Outputs
output "client_vpn_endpoint_id" {
  description = "ID of the Client VPN endpoint"
  value       = var.create_client_vpn ? aws_ec2_client_vpn_endpoint.main[0].id : null
}

output "client_vpn_endpoint_arn" {
  description = "ARN of the Client VPN endpoint"
  value       = var.create_client_vpn ? aws_ec2_client_vpn_endpoint.main[0].arn : null
}

output "client_vpn_endpoint_dns_name" {
  description = "DNS name of the Client VPN endpoint"
  value       = var.create_client_vpn ? aws_ec2_client_vpn_endpoint.main[0].dns_name : null
}

output "client_vpn_network_associations" {
  description = "Map of Client VPN network associations"
  value = var.create_client_vpn ? {
    for k, v in aws_ec2_client_vpn_network_association.main : k => {
      id       = v.id
      subnet_id = v.subnet_id
      status   = v.status
    }
  } : {}
}

output "client_vpn_authorization_rules" {
  description = "Map of Client VPN authorization rules"
  value = var.create_client_vpn ? {
    for k, v in aws_ec2_client_vpn_authorization_rule.main : k => {
      id                    = v.id
      target_network_cidr   = v.target_network_cidr
      authorize_all_groups  = v.authorize_all_groups
    }
  } : {}
}

# Site-to-Site VPN Outputs
output "vpn_gateway_id" {
  description = "ID of the VPN Gateway"
  value       = var.create_site_to_site_vpn ? aws_vpn_gateway.main[0].id : null
}

output "vpn_gateway_arn" {
  description = "ARN of the VPN Gateway"
  value       = var.create_site_to_site_vpn ? aws_vpn_gateway.main[0].arn : null
}

output "customer_gateways" {
  description = "Map of customer gateway configurations"
  value = var.create_site_to_site_vpn ? {
    for k, v in aws_customer_gateway.main : k => {
      id        = v.id
      bgp_asn   = v.bgp_asn
      ip_address = v.ip_address
      type      = v.type
    }
  } : {}
}

output "vpn_connections" {
  description = "Map of VPN connection configurations"
  value = var.create_site_to_site_vpn ? {
    for k, v in aws_vpn_connection.main : k => {
      id                    = v.id
      tunnel1_address       = v.tunnel1_address
      tunnel2_address       = v.tunnel2_address
      tunnel1_preshared_key = v.tunnel1_preshared_key
      tunnel2_preshared_key = v.tunnel2_preshared_key
      status                = v.status
    }
  } : {}
}

# Certificate Outputs
output "client_vpn_server_certificate_arn" {
  description = "ARN of the Client VPN server certificate"
  value       = var.create_client_vpn ? aws_acm_certificate.client_vpn_server[0].arn : null
}

output "client_vpn_client_certificate_arn" {
  description = "ARN of the Client VPN client certificate"
  value       = var.create_client_vpn ? aws_acm_certificate.client_vpn_client[0].arn : null
}

# Log Group Outputs
output "client_vpn_log_group_name" {
  description = "Name of the Client VPN CloudWatch log group"
  value       = var.create_client_vpn && var.enable_connection_logging ? aws_cloudwatch_log_group.client_vpn_logs[0].name : null
}

# VPN Configuration Summary
output "vpn_configuration" {
  description = "Complete VPN configuration summary"
  value = {
    client_vpn_enabled = var.create_client_vpn
    site_to_site_enabled = var.create_site_to_site_vpn
    client_vpn = var.create_client_vpn ? {
      endpoint_id = aws_ec2_client_vpn_endpoint.main[0].id
      dns_name    = aws_ec2_client_vpn_endpoint.main[0].dns_name
      cidr_block  = var.client_vpn_cidr_block
      split_tunnel = var.split_tunnel
      subnet_count = length(var.client_vpn_subnet_ids)
      authorized_networks = var.client_vpn_authorized_networks
    } : null
    site_to_site = var.create_site_to_site_vpn ? {
      vpn_gateway_id = aws_vpn_gateway.main[0].id
      connection_count = length(var.customer_gateways)
      customer_gateways = keys(var.customer_gateways)
    } : null
  }
} 