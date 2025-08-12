# Route53 Module Outputs

output "hosted_zone_id" {
  description = "ID of the Route53 hosted zone"
  value       = var.create_hosted_zone ? aws_route53_zone.main[0].zone_id : null
}

output "hosted_zone_name_servers" {
  description = "Name servers of the Route53 hosted zone"
  value       = var.create_hosted_zone ? aws_route53_zone.main[0].name_servers : null
}

output "hosted_zone_arn" {
  description = "ARN of the Route53 hosted zone"
  value       = var.create_hosted_zone ? aws_route53_zone.main[0].arn : null
}

output "a_record_names" {
  description = "Names of created A records"
  value       = var.create_hosted_zone ? [for record in aws_route53_record.a_records : record.name] : []
}

output "cname_record_names" {
  description = "Names of created CNAME records"
  value       = var.create_hosted_zone ? [for record in aws_route53_record.cname_records : record.name] : []
}

output "mx_record_names" {
  description = "Names of created MX records"
  value       = var.create_hosted_zone ? [for record in aws_route53_record.mx_records : record.name] : []
}

output "txt_record_names" {
  description = "Names of created TXT records"
  value       = var.create_hosted_zone ? [for record in aws_route53_record.txt_records : record.name] : []
}

output "alias_record_names" {
  description = "Names of created alias records"
  value       = var.create_hosted_zone ? [for record in aws_route53_record.alias_records : record.name] : []
}

output "health_check_ids" {
  description = "IDs of created health checks"
  value       = var.create_hosted_zone ? [for check in aws_route53_health_check.main : check.id] : []
}

output "failover_record_names" {
  description = "Names of created failover records"
  value       = var.create_hosted_zone ? [for record in aws_route53_record.failover_records : record.name] : []
} 