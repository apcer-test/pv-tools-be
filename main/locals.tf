########################################
#           LOCAL VALUES               #
########################################

# Fetch current AWS account ID automatically
data "aws_caller_identity" "current" {}

# Fetch current AWS region
data "aws_region" "current" {}

# Auto-lookup ACM certificate for CloudFront (wildcard only - more reliable)
data "aws_acm_certificate" "cloudfront_auto" {
  count    = var.cloudfront_acm_certificate_arn == "" && local.root_domain_for_cert_lookup != "" ? 1 : 0
  provider = aws.us_east_1  # CloudFront requires certificates in us-east-1
  
  domain      = "*.${local.root_domain_for_cert_lookup}"
  statuses    = ["ISSUED"]
  most_recent = true
}

locals {
  # Automatically fetch AWS account ID
  account_id = data.aws_caller_identity.current.account_id
  
  # Current region
  current_region = data.aws_region.current.id
  
  # Common tags
  common_tags = {
    Project     = var.project_name
    Environment = var.env
    ManagedBy   = "Terraform"
  }
  
  # Pipeline trigger tag pattern
  pipeline_trigger_tag = "${var.project_name}-${var.env}-*"
  
  # Extract all CloudFront aliases to determine root domain for certificate lookup
  all_cloudfront_aliases = flatten(concat(
    # From frontends
    [for frontend_key, frontend in var.frontends : 
      try(frontend.cloudfront_aliases, [])
      if try(frontend.create_cloudfront, false) && try(frontend.create, true)
    ],
    
    # From services
    [for service_key, service in var.services : 
      try(service.cloudfront_aliases, [service.domain])
      if try(service.create_cloudfront, false) && var.create_ecs_ecosystem
    ],
    
    # From cdn_distributions (only collect aliases when cdn is actually created)
    [for cdn_key, cdn in var.cdn_distributions : 
      try(cdn.aliases, [])
      if try(cdn.create, true)
    ]
  ))
  
  # Helper variables for domain extraction
  first_domain = length(local.all_cloudfront_aliases) > 0 ? local.all_cloudfront_aliases[0] : ""
  domain_parts = local.first_domain != "" ? split(".", local.first_domain) : []
  parts_count  = length(local.domain_parts)
  
  # Extract root domain from first available alias (e.g., "sub.example.com" -> "example.com", "sub.domain.co.in" -> "domain.co.in")
  root_domain_for_cert_lookup = local.first_domain != "" ? (
    # Handle 3-part TLD patterns (.co.in, .com.au, etc.)
    local.parts_count >= 3 && can(regex("\\.(co|com|net|org|gov|edu|ac)\\.[a-z]{2}$", local.first_domain)) ? 
      join(".", slice(local.domain_parts, local.parts_count - 3, local.parts_count)) :
    # Handle 2-part TLD patterns (.com, .org, etc.)  
    local.parts_count >= 2 ? 
      join(".", slice(local.domain_parts, local.parts_count - 2, local.parts_count)) :
    # Fallback: use as-is
    local.first_domain
  ) : ""
  
  # Determine final certificate ARN (prioritize manual ARN, then ACM module, fallback to automatic wildcard lookup)
  final_cloudfront_certificate_arn = var.cloudfront_acm_certificate_arn != "" ? var.cloudfront_acm_certificate_arn : (
    var.create_acm_certificate ? module.acm[0].certificate_arn : (
      length(data.aws_acm_certificate.cloudfront_auto) > 0 ? data.aws_acm_certificate.cloudfront_auto[0].arn : ""
    )
  )
  
  # Debug info for certificate lookup
  debug_cert_lookup = {
    step_1_domain_extracted     = local.first_domain
    step_2_root_domain         = local.root_domain_for_cert_lookup  
    step_3_wildcard_searched   = local.root_domain_for_cert_lookup != "" ? "*.${local.root_domain_for_cert_lookup}" : ""
    step_4_certificate_found   = length(data.aws_acm_certificate.cloudfront_auto) > 0
    step_5_final_arn_status    = local.final_cloudfront_certificate_arn != "" ? "Certificate Found" : "No Certificate"
    final_certificate_arn      = local.final_cloudfront_certificate_arn
    expected_certificate       = "*.webelight.co.in"
  }
} 