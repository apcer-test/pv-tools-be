# CloudFront Module Outputs

output "cloudfront_distribution_id" {
  description = "The identifier of the CloudFront distribution"
  value       = var.enabled ? aws_cloudfront_distribution.this[0].id : null
}

output "cloudfront_distribution_arn" {
  description = "The ARN of the CloudFront distribution"
  value       = var.enabled ? aws_cloudfront_distribution.this[0].arn : null
}

output "cloudfront_distribution_domain_name" {
  description = "The domain name of the CloudFront distribution"
  value       = var.enabled ? aws_cloudfront_distribution.this[0].domain_name : null
}

output "cloudfront_distribution_hosted_zone_id" {
  description = "The CloudFront distribution's hosted zone ID"
  value       = var.enabled ? aws_cloudfront_distribution.this[0].hosted_zone_id : null
}

output "cloudfront_distribution_status" {
  description = "The current status of the CloudFront distribution"
  value       = var.enabled ? aws_cloudfront_distribution.this[0].status : null
}

output "cloudfront_distribution_etag" {
  description = "The current version of the distribution's information"
  value       = var.enabled ? aws_cloudfront_distribution.this[0].etag : null
}

output "origin_access_control_id" {
  description = "The identifier of the Origin Access Control"
  value       = var.enabled && var.create_origin_access_control && length(aws_cloudfront_origin_access_control.this) > 0 ? aws_cloudfront_origin_access_control.this[0].id : null
}

output "distribution_config" {
  description = "Complete distribution configuration for reference"
  value = var.enabled ? {
    id          = aws_cloudfront_distribution.this[0].id
    domain_name = aws_cloudfront_distribution.this[0].domain_name
    status      = aws_cloudfront_distribution.this[0].status
    aliases     = aws_cloudfront_distribution.this[0].aliases
    price_class = aws_cloudfront_distribution.this[0].price_class
  } : null
}

output "cloudfront_aliases" {
  description = "The aliases (CNAMEs) of the CloudFront distribution"
  value       = var.enabled ? aws_cloudfront_distribution.this[0].aliases : []
} 