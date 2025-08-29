# CloudFront Distribution Module

# Origin Access Control for S3
resource "aws_cloudfront_origin_access_control" "this" {
  count = var.create_origin_access_control ? 1 : 0

  name                              = "${var.project_name}-${var.app_name}-oac-${var.env}"
  description                       = "Origin Access Control for ${var.project_name}-${var.app_name}-${var.env}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# Local values for computed configurations
locals {
  certificate_arn = var.viewer_certificate_arn != "" ? var.viewer_certificate_arn : var.acm_certificate_arn
  domain_names    = length(var.aliases) > 0 ? var.aliases : var.alternate_domain_names
  
  # Default cache behavior configuration
  default_cache_behavior = var.default_cache_behavior != null ? var.default_cache_behavior : {
    target_origin_id       = var.origin_id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "this" {
  count = var.enabled ? 1 : 0

  # Origin Configuration
  origin {
    domain_name = var.origin_domain_name
    origin_id   = var.origin_id
    origin_path = var.origin_path

    # Use OAC for S3 origins, custom origin config for ALB/API origins or website endpoints
    origin_access_control_id = var.create_origin_access_control && !var.is_website_endpoint ? aws_cloudfront_origin_access_control.this[0].id : null

    dynamic "custom_origin_config" {
      for_each = (var.create_origin_access_control && !var.is_website_endpoint) ? [] : [1]
      content {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = var.origin_protocol_policy
        origin_ssl_protocols   = ["TLSv1.2"]
      }
    }
  }

  # Distribution Settings
  enabled             = true
  is_ipv6_enabled     = true
  comment             = var.comment
  default_root_object = var.default_root_object

  # Alternate Domain Names
  aliases = local.domain_names

  # Default Cache Behavior
  default_cache_behavior {
    allowed_methods            = local.default_cache_behavior.allowed_methods
    cached_methods             = local.default_cache_behavior.cached_methods
    target_origin_id           = local.default_cache_behavior.target_origin_id
    compress                   = local.default_cache_behavior.compress
    viewer_protocol_policy     = local.default_cache_behavior.viewer_protocol_policy

    # TTL Settings
    min_ttl     = local.default_cache_behavior.min_ttl
    default_ttl = local.default_cache_behavior.default_ttl
    max_ttl     = local.default_cache_behavior.max_ttl

    # Response Headers Policy for CORS (mutually exclusive with forwarded_values)
    response_headers_policy_id = var.response_headers_policy_id != "" ? var.response_headers_policy_id : null

    # Forwarded Values - Use variable or default for ALB origins (only when no response headers policy)
    dynamic "forwarded_values" {
      for_each = var.response_headers_policy_id == "" ? [1] : []
      content {
        query_string = try(var.forwarded_values.query_string, false)
        headers      = try(var.forwarded_values.headers, [])
        cookies {
          forward           = try(var.forwarded_values.cookies.forward, "none")
          whitelisted_names = try(var.forwarded_values.cookies.whitelisted_names, [])
        }
      }
    }
  }

  # Custom Error Response
  dynamic "custom_error_response" {
    for_each = var.error_pages
    content {
      error_code         = custom_error_response.value.error_code
      response_code      = custom_error_response.value.response_code
      response_page_path = custom_error_response.value.response_page_path
    }
  }

  # Viewer Certificate
  viewer_certificate {
    # Use ACM certificate if provided, otherwise use default CloudFront certificate
    acm_certificate_arn      = local.certificate_arn != "" ? local.certificate_arn : null
    cloudfront_default_certificate = local.certificate_arn == "" ? true : false
    ssl_support_method       = local.certificate_arn != "" ? "sni-only" : null
    minimum_protocol_version = local.certificate_arn != "" ? "TLSv1.2_2021" : null
  }

  # Price Class
  price_class = var.price_class

  # WAF Web ACL Association
  web_acl_id = var.web_acl_arn != "" ? var.web_acl_arn : null

  # Geographic Restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Tags
  tags = merge(
    {
      Name        = var.cloudfront_distribution_name
      Project     = var.project_name
      Environment = var.env
      Service     = "cloudfront"
      Terraform   = "true"
    }
  )
}

 