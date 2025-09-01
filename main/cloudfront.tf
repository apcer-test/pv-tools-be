# Create RSA key pair for CloudFront signed cookies (only for media service)
locals {
  # Temporarily disable key creation due to AWS limit - can be re-enabled later
  has_media_service = false
  # Auto-detects CloudFront need based on individual configurations
  #   for frontend_key, frontend in var.frontends : frontend.service_name == "media" && try(frontend.enable_signed_cookies, false) && try(frontend.create_cloudfront, false)
  # ])
}



resource "tls_private_key" "cloudfront_key" {
  count     = local.has_media_service ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = 2048
}

# Upload public key to CloudFront
resource "aws_cloudfront_public_key" "cloudfront_key" {
  count           = local.has_media_service ? 1 : 0
  comment         = "Public key for CloudFront signed cookies"
  encoded_key     = tls_private_key.cloudfront_key[0].public_key_pem
  name            = "${var.project_name}-${var.env}-cloudfront-key"
}

# Create CloudFront key group
resource "aws_cloudfront_key_group" "cloudfront_key_group" {
  count   = local.has_media_service ? 1 : 0
  comment = "Key group for CloudFront signed cookies"
  items   = [aws_cloudfront_public_key.cloudfront_key[0].id]
  name    = "${var.project_name}-${var.env}-cloudfront-key-group"
}

# Private key is available via terraform output only

# output the key ID for reference
output "cloudfront_key_id" {
  description = "CloudFront public key ID"
  value       = local.has_media_service ? aws_cloudfront_public_key.cloudfront_key[0].id : null
}

output "cloudfront_key_group_id" {
  description = "CloudFront key group ID"
  value       = local.has_media_service ? aws_cloudfront_key_group.cloudfront_key_group[0].id : null
}

output "cloudfront_private_key" {
  description = "Private key for signing CloudFront cookies (keep secure!)"
  value       = local.has_media_service ? tls_private_key.cloudfront_key[0].private_key_pem : null
  sensitive   = true
}

output "cloudfront_public_key" {
  description = "Public key content"
  value       = local.has_media_service ? tls_private_key.cloudfront_key[0].public_key_pem : null
}



output "certificate_arn_used" {
  description = "The certificate ARN being used for CloudFront distributions"
  value       = var.cloudfront_acm_certificate_arn
}



# Auto-generate CloudFront distributions with static defaults
locals {
  # Frontend-specific CloudFront distributions (S3 origin)
  # Only create CloudFront for frontends that are actually being created AND have create_cloudfront = true
  frontend_cloudfront_distributions = {
    for frontend_key, frontend in var.frontends : "${frontend_key}-cloudfront" => {
      service_name        = frontend.service_name
      
      origin_type         = "s3"
      aliases             = length(try(frontend.cloudfront_aliases, [])) > 0 ? frontend.cloudfront_aliases : [frontend.domain]
      default_root_object = try(frontend.default_root_object, "index.html")
      error_pages         = try(frontend.error_pages, [])  # Allow frontend-specific error page overrides
      forwarded_values    = try(frontend.cloudfront_forwarded_values, {
        query_string = false
        headers      = []
        cookies = {
          forward = "none"
        }
      })
      bucket_key          = "${frontend.service_name}_bucket"  # Reference to S3 bucket
      enable_website      = try(frontend.enable_website, false)  # Pass website configuration
    } if try(frontend.create_cloudfront, false) && try(frontend.create, true) && contains(keys(local.s3_buckets), "${frontend.service_name}_bucket")
  }
  # Service-specific CloudFront distributions (ALB origin)
  # Only create CloudFront for services that are actually being created AND have create_cloudfront = true
  # AND when ECS ecosystem is being targeted
  # Services always use optimal ALB forwarding - not configurable via tfvars
  service_cloudfront_distributions = {
    for service_key, service in var.services : "${service_key}-cloudfront" => {
      service_name        = service.container_name
      origin_type         = "alb"
      # Auto-use domain as CloudFront alias when create_cloudfront = true
      # cloudfront_aliases can override if needed for advanced cases
      aliases             = length(try(service.cloudfront_aliases, [])) > 0 ? service.cloudfront_aliases : [service.domain]
      forwarded_values    = {
        query_string = true
        headers      = ["*"]
        cookies = {
          forward = "all"
        }
      }
    } if try(service.create_cloudfront, false) && var.create_ecs_ecosystem
  }
  
  # Infrastructure bucket CloudFront distributions (S3 origin)
  # Create CloudFront for infrastructure buckets that have enable_oac = true
  infrastructure_cloudfront_distributions = {
    for bucket_key, bucket in var.storage_buckets : "${bucket.service_name}-cloudfront" => {
      service_name        = bucket.service_name
      origin_type         = "s3"
      aliases             = try(bucket.cloudfront_aliases, [])
      default_root_object = try(bucket.default_root_object, "index.html")
      forwarded_values    = try(bucket.cloudfront_forwarded_values, {
        query_string = false
        headers      = []
        cookies = {
          forward = "none"
        }
      })
      bucket_key          = bucket_key  # Reference to S3 bucket
    } if try(bucket.create, true) && try(bucket.enable_oac, false) && contains(["admin", "media"], bucket.service_name)
  }
  
  # Check if any S3 buckets need CloudFront access (have enable_oac = true)
  s3_buckets_need_cloudfront = anytrue([
    for bucket_key, bucket in var.storage_buckets : 
    try(bucket.enable_oac, false) if try(bucket.create, true)
  ])
  
  # Check if any frontends need CloudFront access (have create_cloudfront = true)
  frontends_need_cloudfront = anytrue([
    for frontend_key, frontend in var.frontends : 
    try(frontend.create_cloudfront, false) if try(frontend.create, true)
  ])
  
  # Check if any services need CloudFront access (have create_cloudfront = true)
  services_need_cloudfront = anytrue([
    for service_key, service in var.services : 
    try(service.create_cloudfront, false) if var.create_ecs_ecosystem
  ])
  
  # Auto-detect if CloudFront is needed anywhere
  auto_create_cloudfront = local.frontends_need_cloudfront || local.services_need_cloudfront || local.s3_buckets_need_cloudfront
  
  # Combine cdn_distributions, frontend, service-specific, and infrastructure distributions
  # Include cdn_distributions when CloudFront is needed anywhere
  all_cloudfront_distributions = merge(
    local.auto_create_cloudfront ? var.cdn_distributions : {}, 
    local.frontend_cloudfront_distributions,
    local.service_cloudfront_distributions,
    local.infrastructure_cloudfront_distributions
  )
  
  cloudfront_distributions = {
    for cdn_key, cdn in local.all_cloudfront_distributions : cdn_key => merge(cdn, {
      # Auto-generate origin_id based on service_name and origin_type
      origin_id = cdn.origin_type == "s3" ? "S3-${var.project_name}-${cdn.service_name}-${var.env}" : "ALB-${var.project_name}-${cdn.service_name}-${var.env}",
      
      # Auto-generate error pages for S3 origins (frontend SPAs)
      # Use the actual default_root_object from the distribution
      error_pages = try(cdn.error_pages, null) != null ? cdn.error_pages : (cdn.origin_type == "s3" ? [
        {
          error_code            = 403
          response_code         = "200"
          response_page_path    = "/${cdn.default_root_object}"
          error_caching_min_ttl = 30
        },
        {
          error_code            = 404
          response_code         = "200"
          response_page_path    = "/${cdn.default_root_object}"
          error_caching_min_ttl = 30
        }
      ] : []),
      
      # Auto-generate default_cache_behavior with consistent types
      default_cache_behavior = try(cdn.default_cache_behavior, null) != null ? {
        target_origin_id       = cdn.default_cache_behavior.target_origin_id
        viewer_protocol_policy = cdn.default_cache_behavior.viewer_protocol_policy
        allowed_methods        = tolist(cdn.default_cache_behavior.allowed_methods)
        cached_methods         = tolist(cdn.default_cache_behavior.cached_methods)
        compress               = cdn.default_cache_behavior.compress
        min_ttl                = cdn.default_cache_behavior.min_ttl
        default_ttl            = cdn.default_cache_behavior.default_ttl
        max_ttl                = cdn.default_cache_behavior.max_ttl
        trusted_key_groups     = tolist(try(cdn.default_cache_behavior.trusted_key_groups, (cdn.service_name == "media" && local.has_media_service) ? [aws_cloudfront_key_group.cloudfront_key_group[0].id] : []))
        forwarded_values       = cdn.default_cache_behavior.forwarded_values
      } : (cdn.origin_type == "s3" ? {
        target_origin_id       = "S3-${var.project_name}-${cdn.service_name}-${var.env}"
        viewer_protocol_policy = "redirect-to-https"
        allowed_methods        = tolist(["GET", "HEAD", "OPTIONS"])
        cached_methods         = tolist(["GET", "HEAD"])
        compress               = true
        min_ttl                = 0
        default_ttl            = 3600
        max_ttl                = 86400
        trusted_key_groups     = tolist((cdn.service_name == "media" && local.has_media_service) ? [aws_cloudfront_key_group.cloudfront_key_group[0].id] : [])
        forwarded_values = try(cdn.forwarded_values, {
          query_string = false
          headers      = tolist([])
          cookies = {
            forward = "none"
          }
        })
      } : {
        target_origin_id       = "ALB-${var.project_name}-${cdn.service_name}-${var.env}"
        viewer_protocol_policy = "redirect-to-https"
        allowed_methods        = tolist(["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"])
        cached_methods         = tolist(["GET", "HEAD"])
        compress               = true
        min_ttl                = 0
        default_ttl            = 0
        max_ttl                = 0
        trusted_key_groups     = tolist((cdn.service_name == "media" && local.has_media_service) ? [aws_cloudfront_key_group.cloudfront_key_group[0].id] : [])
        forwarded_values = try(cdn.forwarded_values, {
          query_string = true
          headers      = tolist(["*"])
          cookies = {
            forward = "all"
          }
        })
      }),
      
      # Additional CloudFront module properties
      project_name                  = var.project_name
      app_name                      = cdn.service_name
      env                           = var.env
      enabled                       = try(cdn.create, true)
      cloudfront_distribution_name  = "${var.project_name}-${cdn.service_name}-${var.env}"
      # Dynamically set origin_domain_name based on origin_type
      origin_domain_name            = cdn.origin_type == "s3" ? (
        # For frontend CloudFronts, use bucket_key to reference S3 bucket
        try(cdn.bucket_key, null) != null ? 
          (try(module.s3[cdn.bucket_key].website_endpoint, null) != null ? module.s3[cdn.bucket_key].website_endpoint : "${module.s3[cdn.bucket_key].bucket_name}.s3.${var.region}.amazonaws.com") :
          # Fallback for old-style bucket references
          (try(module.s3["${cdn.service_name}_bucket"].website_endpoint, null) != null ? module.s3["${cdn.service_name}_bucket"].website_endpoint : "${module.s3["${cdn.service_name}_bucket"].bucket_name}.s3.${var.region}.amazonaws.com")
      ) : (cdn.origin_type == "alb" ? try(module.ecs-alb.alb_dns_name, "") : try(cdn.origin_domain_name, ""))
      origin_path                   = try(cdn.origin_path, "")
      origin_protocol_policy        = try(cdn.protocol_policy, "http-only")  # Use HTTP-only for both S3 and ALB origins
      viewer_certificate_arn        = try(cdn.certificate_arn, "")
      acm_certificate_arn           = var.cloudfront_acm_certificate_arn
      alternate_domain_names        = try(cdn.aliases, [])
      default_root_object           = try(cdn.default_root_object, "")
      price_class                   = try(cdn.price_class, "PriceClass_100")
      comment                       = "CloudFront distribution for ${cdn.service_name} service"
      tags = {
        Environment = var.env
        Service     = cdn.service_name
        Project     = var.project_name
      }
    })
  }
}

# Debug output to check aliases
output "debug_frontend_aliases" {
  description = "Debug: Frontend CloudFront aliases"
  value = {
    for cdn_key, cdn in local.cloudfront_distributions : cdn_key => {
      aliases = cdn.aliases
      alternate_domain_names = cdn.alternate_domain_names
    } if contains(keys(local.frontend_cloudfront_distributions), cdn_key)
  }
}

output "debug_frontend_config" {
  description = "Debug: Frontend configuration"
  value = {
    for frontend_key, frontend in var.frontends : frontend_key => {
      cloudfront_aliases = try(frontend.cloudfront_aliases, [])
      create_cloudfront = frontend.create_cloudfront
      create = frontend.create
    }
  }
}

output "debug_media_config" {
  description = "Debug: Media configuration"
  value = {
    for frontend_key, frontend in var.storage_buckets : frontend_key => {
      cloudfront_aliases = try(frontend.cloudfront_aliases, [])
      #create_cloudfront = frontend.create_cloudfront
      #create = frontend.create
    }
  }
}

# Create CloudFront distributions for S3 buckets (admin/media)
# Create when targeting S3 + CloudFront OR when infrastructure buckets need CloudFront access
module "cloudfront_s3" {
  for_each = {
    for cdn_key, cdn in local.cloudfront_distributions : cdn_key => cdn
    if local.auto_create_cloudfront && cdn.origin_type == "s3"
  }
  source   = "../modules/cloudfront"
  
  project_name                  = each.value.project_name
  app_name                      = each.value.app_name
  env                           = each.value.env
  enabled                       = each.value.enabled
  cloudfront_distribution_name  = each.value.cloudfront_distribution_name
  aliases                       = each.value.aliases
  origin_domain_name            = each.value.origin_domain_name
  origin_id                     = each.value.origin_id
  origin_path                   = each.value.origin_path
  origin_protocol_policy        = each.value.origin_protocol_policy
  viewer_certificate_arn        = each.value.viewer_certificate_arn
  acm_certificate_arn           = var.cloudfront_acm_certificate_arn
  alternate_domain_names        = each.value.alternate_domain_names
  default_root_object           = each.value.default_root_object
  price_class                   = each.value.price_class
  comment                       = each.value.comment
  error_pages                   = each.value.error_pages
  default_cache_behavior        = each.value.default_cache_behavior
  create_origin_access_control  = contains(["frontend", "media"], each.value.service_name)  # Enable OAC only for frontend and media
  is_website_endpoint           = try(each.value.enable_website, false)  # Use custom origin for website endpoints
  tags                          = each.value.tags
}

# Response Headers Policy for CORS
resource "aws_cloudfront_response_headers_policy" "cors_policy" {
  count = local.services_need_cloudfront ? 1 : 0
  
  name    = "${var.project_name}-${var.env}-cors-policy"
  comment = "CORS policy for API CloudFront distribution"

  cors_config {
    access_control_allow_credentials = true
    access_control_allow_headers {
      items = [
        "Origin",
        "Content-Type",
        "Accept",
        "Authorization",
        "X-Requested-With",
        "Access-Control-Request-Method",
        "Cookie",
        "Access-Control-Request-Headers"
      ]
    }
    access_control_allow_methods {
      items = [
        "GET",
        "HEAD",
        "PUT",
        "PATCH",
        "POST",
        "DELETE",
        "OPTIONS"
      ]
    }
    access_control_allow_origins {
      items = [
        "http://localhost",
        "http://localhost:5173",
        "https://viper-related-foal.ngrok-free.app",
        "https://fe-dev.apcerls.com"
      ]
    }
    access_control_expose_headers {
      items = []
    }
    access_control_max_age_sec = 600
    origin_override = true
  }

  security_headers_config {
    content_type_options {
      override = true
    }
    frame_options {
      frame_option = "SAMEORIGIN"
      override     = true
    }
    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      override                   = true
      preload                    = true
    }
  }
}


# Create CloudFront distributions for ECS services
# Only create when targeting ECS + CloudFront
module "cloudfront_ecs" {
  for_each = {
    for cdn_key, cdn in local.cloudfront_distributions : cdn_key => cdn
    if local.services_need_cloudfront && var.create_ecs_ecosystem && cdn.origin_type == "alb"
  }
  source   = "../modules/cloudfront"
  
  project_name                  = each.value.project_name
  app_name                      = each.value.app_name
  env                           = each.value.env
  enabled                       = each.value.enabled
  cloudfront_distribution_name  = each.value.cloudfront_distribution_name
  aliases                       = each.value.aliases
  origin_domain_name            = each.value.origin_domain_name
  origin_id                     = each.value.origin_id
  origin_path                   = each.value.origin_path
  origin_protocol_policy        = each.value.origin_protocol_policy
  viewer_certificate_arn        = each.value.viewer_certificate_arn
  acm_certificate_arn           = var.cloudfront_acm_certificate_arn
  alternate_domain_names        = each.value.alternate_domain_names
  default_root_object           = each.value.default_root_object
  price_class                   = each.value.price_class
  comment                       = each.value.comment
  error_pages                   = each.value.error_pages
  default_cache_behavior        = each.value.default_cache_behavior
  forwarded_values              = each.value.default_cache_behavior.forwarded_values
  create_origin_access_control  = false  # ECS services use ALB, not S3
  response_headers_policy_id    = aws_cloudfront_response_headers_policy.cors_policy[0].id
  tags                          = each.value.tags
} 