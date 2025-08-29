# Extract ECS service names for dynamic microservices folder creation
locals {
  # Extract container names from ECS services
  ecs_service_names = var.create_ecs_ecosystem ? [for service_key, service in var.services : service.container_name] : []
  
  # Map bucket service names to CloudFront distribution ARNs
  # Use empty string initially, will be updated after CloudFront creation
  bucket_to_cloudfront_arn = {
    "admin" = ""
    "media" = ""
  }
  
  # Helper locals for bucket existence checks
  has_env_bucket = contains(keys(var.storage_buckets), "env_bucket") && try(var.storage_buckets["env_bucket"].create, true)
  has_codepipeline_bucket = contains(keys(var.storage_buckets), "codepipeline_artifacts_bucket") && try(var.storage_buckets["codepipeline_artifacts_bucket"].create, true)
  
  # Frontend-specific bucket checks
  has_admin_frontend = anytrue([for key, frontend in var.frontends : frontend.service_name == "admin" && try(frontend.create, true)])
  has_media_frontend = anytrue([for key, frontend in var.frontends : frontend.service_name == "media" && try(frontend.create, true)])
  
  # Generate S3 buckets from frontends configuration
  frontend_buckets = {
    for frontend_key, frontend in var.frontends : "${frontend.service_name}_bucket" => {
      bucket_name        = "${var.project_name}-${frontend.service_name}-${var.env}"
      project_name       = var.project_name
      env               = var.env
      index_document    = try(frontend.index_document, var.s3_index_document)
      error_document    = try(frontend.error_document, var.s3_error_document)
      acl               = var.s3_acl
      cors_rules        = [
        for rule in try(frontend.cors_rules, []) : {
          allowed_headers = ["*"]                                    # Static default
          allowed_methods = rule.allowed_methods                     # From tfvars
          allowed_origins = rule.allowed_origins                     # From tfvars
          expose_headers  = ["ETag", "Content-Length"]              # Static default
          max_age_seconds = 3600                                     # Static default
        }
      ]
      enable_acl        = false
      enable_encryption = try(frontend.enable_encryption, false)
      enable_cors       = try(frontend.cors_rules, null) != null && length(try(frontend.cors_rules, [])) > 0
      enable_versioning = try(frontend.enable_versioning, false)
      enable_website    = try(frontend.enable_website, false)
      app_name          = var.app_name
      microservices     = []  # Frontend buckets don't have microservices folders
      environments      = [var.env]
      service_folders   = []  # Frontend buckets don't have service folders
      enable_oac        = try(frontend.enable_oac, false)
      # Lifecycle configuration
      enable_lifecycle = try(frontend.lifecycle_rules, null) != null && length(try(frontend.lifecycle_rules, [])) > 0
      lifecycle_rules  = try(frontend.lifecycle_rules, [])
      service_name      = frontend.service_name  # For CloudFront reference
    } if try(frontend.create, true)
  }

  # Auto-generate S3 buckets from infrastructure storage configuration
  # Note: CodePipeline artifacts bucket is only created when create_codepipelines = true
  infrastructure_buckets = {
    for bucket_key, bucket in var.storage_buckets : bucket_key => {
      bucket_name     = "${var.project_name}-${bucket.service_name}-${var.env}"
      project_name    = var.project_name
      env            = var.env
      index_document = var.s3_index_document
      error_document = var.s3_error_document
      acl            = var.s3_acl
      cors_rules     = [
        for rule in try(bucket.cors_rules, []) : {
          allowed_headers = ["*"]                                    # Static default
          allowed_methods = rule.allowed_methods                     # From tfvars
          allowed_origins = rule.allowed_origins                     # From tfvars
          expose_headers  = ["ETag", "Content-Length"]              # Static default
          max_age_seconds = 3600                                     # Static default
        }
      ]
      enable_acl         = false
      enable_encryption  = try(bucket.enable_encryption, false)
      enable_cors        = try(bucket.cors_rules, null) != null && length(try(bucket.cors_rules, [])) > 0
      enable_versioning  = try(bucket.enable_versioning, false)
      enable_website     = try(bucket.enable_website, false)
      app_name          = var.app_name
      # Only create microservices folders in env bucket
      microservices     = bucket.service_name == "env" ? (length(local.ecs_service_names) > 0 ? [for service in local.ecs_service_names : service if service != "api"] : try(bucket.microservices, [])) : []
      environments      = [var.env]
      # Only create service folders in env bucket (admin, api)
      service_folders   = bucket.service_name == "env" ? try(bucket.service_folders, []) : []
      # OAC configuration for buckets that need CloudFront access
      enable_oac       = try(bucket.enable_oac, false)
      # Lifecycle configuration
      enable_lifecycle = try(bucket.lifecycle_rules, null) != null && length(try(bucket.lifecycle_rules, [])) > 0
      lifecycle_rules  = try(bucket.lifecycle_rules, [])
      service_name      = bucket.service_name  # For reference
    } if try(bucket.create, true) && (
      # Only create artifacts bucket when pipelines are enabled
      bucket_key == "codepipeline_artifacts_bucket" ? var.create_codepipelines : true
    )
  }
  
  # Combine frontend and infrastructure buckets
  s3_buckets = merge(local.frontend_buckets, local.infrastructure_buckets)
}

# Create S3 buckets from master configuration (only create buckets that exist in storage_buckets)
module "s3" {
  for_each = local.s3_buckets  # No global create_s3 flag - individual bucket control
  source   = "../modules/s3"
  
  bucket_name     = each.value.bucket_name
  project_name    = each.value.project_name
  env            = each.value.env
  index_document = each.value.index_document
  error_document = each.value.error_document
  acl            = each.value.acl
  cors_rules     = each.value.cors_rules
  enable_acl         = each.value.enable_acl
  enable_encryption  = each.value.enable_encryption
  enable_cors        = each.value.enable_cors
  enable_versioning  = each.value.enable_versioning
  enable_website     = each.value.enable_website
  app_name          = each.value.app_name
  microservices     = each.value.microservices
  environments      = each.value.environments
  service_folders   = each.value.service_folders
  enable_oac        = each.value.enable_oac
  enable_lifecycle  = each.value.enable_lifecycle
  lifecycle_rules   = each.value.lifecycle_rules
}

# Update S3 bucket policies with CloudFront ARNs after CloudFront creation  
# Create policies for both frontend and infrastructure buckets that have CloudFront enabled
resource "aws_s3_bucket_policy" "oac_policies" {
  for_each = merge(
    # Frontend bucket policies
    {
      for frontend_key, frontend in var.frontends : "${frontend.service_name}_bucket" => {
        bucket_key = "${frontend.service_name}_bucket"
        service_name = frontend.service_name
        cloudfront_key = "${frontend_key}-cloudfront"
        bucket_type = "frontend"
      } if try(frontend.create, true) && try(frontend.create_cloudfront, false) && try(frontend.enable_oac, false)
    },
    # Infrastructure bucket policies (like media bucket from storage_buckets)
    {
      for bucket_key, bucket in var.storage_buckets : bucket_key => {
        bucket_key = bucket_key
        service_name = bucket.service_name
        cloudfront_key = "${bucket.service_name}-cloudfront"
        bucket_type = "infrastructure"
      } if try(bucket.create, true) && try(bucket.enable_oac, false) && contains(["admin", "media"], bucket.service_name)
    }
  )
  
  bucket = module.s3[each.key].bucket_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontServicePrincipal"
        Effect    = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${module.s3[each.key].bucket_arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = module.cloudfront_s3[each.value.cloudfront_key].cloudfront_distribution_arn
          }
        }
      }
    ]
  })

  depends_on = [module.s3, module.cloudfront_s3]
}

