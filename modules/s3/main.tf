# S3 Bucket Module

# Main S3 Bucket
resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name

  tags = merge(
    {
      Name        = var.bucket_name
      Project     = var.project_name
      Environment = var.env
      Service     = "s3"
      Terraform   = "true"
    },
    var.tags
  )
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "this" {
  count  = var.enable_versioning ? 1 : 0
  bucket = aws_s3_bucket.this.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  count  = var.enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "this" {
  count  = var.block_public_access ? 1 : 0
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket ACL
resource "aws_s3_bucket_acl" "this" {
  count      = var.enable_acl ? 1 : 0
  bucket     = aws_s3_bucket.this.id
  acl        = var.acl
  depends_on = [aws_s3_bucket_ownership_controls.this]
}

# S3 Bucket Ownership Controls
resource "aws_s3_bucket_ownership_controls" "this" {
  count  = var.enable_acl ? 1 : 0
  bucket = aws_s3_bucket.this.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# S3 Bucket Website Configuration
resource "aws_s3_bucket_website_configuration" "this" {
  count  = var.enable_website ? 1 : 0
  bucket = aws_s3_bucket.this.id

  index_document {
    suffix = var.index_document
  }

  error_document {
    key = var.error_document
  }
}

# S3 Bucket CORS Configuration
resource "aws_s3_bucket_cors_configuration" "this" {
  count  = var.enable_cors && length(var.cors_rules) > 0 ? 1 : 0
  bucket = aws_s3_bucket.this.id

  dynamic "cors_rule" {
    for_each = var.cors_rules
    content {
      allowed_headers = cors_rule.value.allowed_headers
      allowed_methods = cors_rule.value.allowed_methods
      allowed_origins = cors_rule.value.allowed_origins
      expose_headers  = cors_rule.value.expose_headers
      max_age_seconds = cors_rule.value.max_age_seconds
    }
  }
}

# Origin Access Control for CloudFront
resource "aws_cloudfront_origin_access_control" "this" {
  count                              = var.enable_oac ? 1 : 0
  name                               = "${var.bucket_name}-oac"
  description                        = "Origin Access Control for ${var.bucket_name}"
  origin_access_control_origin_type  = "s3"
  signing_behavior                   = "always"
  signing_protocol                   = "sigv4"
}

# Note: OAC bucket policies are now handled in main/s3.tf to avoid circular dependencies

# S3 Bucket Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  count  = var.enable_lifecycle && length(var.lifecycle_rules) > 0 ? 1 : 0
  bucket = aws_s3_bucket.this.id

  dynamic "rule" {
    for_each = var.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      filter {
        prefix = rule.value.filter_prefix
      }

      # Expiration
      dynamic "expiration" {
        for_each = rule.value.expiration_days > 0 ? [1] : []
        content {
          days = rule.value.expiration_days
        }
      }

      # Noncurrent version expiration
      dynamic "noncurrent_version_expiration" {
        for_each = rule.value.noncurrent_version_expiration_days > 0 ? [1] : []
        content {
          noncurrent_days = rule.value.noncurrent_version_expiration_days
        }
      }

      # Transition to IA
      dynamic "transition" {
        for_each = rule.value.transition_to_ia_days > 0 ? [1] : []
        content {
          days          = rule.value.transition_to_ia_days
          storage_class = "STANDARD_IA"
        }
      }

      # Transition to Glacier
      dynamic "transition" {
        for_each = rule.value.transition_to_glacier_days > 0 ? [1] : []
        content {
          days          = rule.value.transition_to_glacier_days
          storage_class = "GLACIER"
        }
      }
    }
  }
}

# General Folders
resource "aws_s3_object" "folders" {
  for_each = toset(var.folder_paths)
  bucket   = aws_s3_bucket.this.id
  key      = "${each.value}/"
  content  = ""
}

# Service Folders with Environment Subfolders
resource "aws_s3_object" "service_folders" {
  for_each = toset([
    for pair in setproduct(var.service_folders, var.environments) : "${pair[0]}/${pair[1]}"
  ])
  bucket  = aws_s3_bucket.this.id
  key     = "${each.value}/"
  content = ""
}

# Microservices Folders with Environment Subfolders
resource "aws_s3_object" "microservices_folders" {
  for_each = toset([
    for pair in setproduct(var.microservices, var.environments) : "microservices/${pair[0]}/${pair[1]}"
  ])
  bucket  = aws_s3_bucket.this.id
  key     = "${each.value}/"
  content = ""
} 