# ACM Module Outputs for Regional Certificates

output "certificate_arn" {
  description = "ARN of the regional certificate"
  value       = var.create_regional_certificate ? aws_acm_certificate.regional[0].arn : null
}

output "certificate_id" {
  description = "ID of the regional certificate"
  value       = var.create_regional_certificate ? aws_acm_certificate.regional[0].id : null
}

output "certificate_domain_name" {
  description = "Domain name of the regional certificate"
  value       = var.create_regional_certificate ? aws_acm_certificate.regional[0].domain_name : null
}

output "validation_record_fqdns" {
  description = "FQDNs of validation records"
  value       = var.create_regional_certificate ? [for record in aws_route53_record.regional_validation : record.fqdn] : []
} 