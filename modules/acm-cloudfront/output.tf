# ACM CloudFront Module Outputs

output "certificate_arn" {
  description = "ARN of the CloudFront certificate"
  value       = var.create_certificate ? aws_acm_certificate.cloudfront[0].arn : null
}

output "certificate_id" {
  description = "ID of the CloudFront certificate"
  value       = var.create_certificate ? aws_acm_certificate.cloudfront[0].id : null
}

output "certificate_domain_name" {
  description = "Domain name of the CloudFront certificate"
  value       = var.create_certificate ? aws_acm_certificate.cloudfront[0].domain_name : null
}

output "validation_record_fqdns" {
  description = "FQDNs of validation records"
  value       = var.create_certificate ? [for record in aws_route53_record.cloudfront_validation : record.fqdn] : []
} 