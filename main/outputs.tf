# S3 Bucket Outputs
output "s3_bucket_arns" {
  description = "ARNs of all S3 buckets"
  value = {
    for bucket_key, bucket in module.s3 : bucket_key => bucket.bucket_arn
  }
}

output "admin_bucket_arn" {
  description = "ARN of the admin S3 bucket"
  value = try(module.s3["admin_bucket"].bucket_arn, "")
}

output "media_bucket_arn" {
  description = "ARN of the media S3 bucket"
  value = try(module.s3["media_bucket"].bucket_arn, "")
}

output "env_bucket_arn" {
  description = "ARN of the environment S3 bucket"
  value = try(module.s3["env_bucket"].bucket_arn, "")
}

# CloudFront Distribution Outputs
output "cloudfront_distribution_arns" {
  description = "ARNs of all CloudFront distributions"
  value = merge(
    {
      for cdn_key, cdn in module.cloudfront_s3 : cdn_key => cdn.cloudfront_distribution_arn
    },
    {
      for cdn_key, cdn in module.cloudfront_ecs : cdn_key => cdn.cloudfront_distribution_arn
    }
  )
}

output "admin_cloudfront_arn" {
  description = "ARN of the admin CloudFront distribution"
  value = try(module.cloudfront_s3["admin-cloudfront"].cloudfront_distribution_arn, "")
}

output "media_cloudfront_arn" {
  description = "ARN of the media CloudFront distribution"
  value = try(module.cloudfront_s3["media-cloudfront"].cloudfront_distribution_arn, "")
}

output "api_cloudfront_arn" {
  description = "ARN of the API CloudFront distribution"
  value = try(module.cloudfront_ecs["service1-cloudfront"].cloudfront_distribution_arn, "")
}

output "notification_cloudfront_arn" {
  description = "ARN of the notification CloudFront distribution"
  value = try(module.cloudfront_ecs["service4-cloudfront"].cloudfront_distribution_arn, "")
}

# CloudFront Domain Names
output "cloudfront_domain_names" {
  description = "Domain names of all CloudFront distributions"
  value = merge(
    {
      for cdn_key, cdn in module.cloudfront_s3 : cdn_key => cdn.cloudfront_distribution_domain_name
    },
    {
      for cdn_key, cdn in module.cloudfront_ecs : cdn_key => cdn.cloudfront_distribution_domain_name
    }
  )
}

output "admin_cloudfront_domain" {
  description = "Domain name of the admin CloudFront distribution"
  value = try(module.cloudfront_s3["admin-cloudfront"].cloudfront_distribution_domain_name, "")
}

output "media_cloudfront_domain" {
  description = "Domain name of the media CloudFront distribution"
  value = try(module.cloudfront_s3["media-cloudfront"].cloudfront_distribution_domain_name, "")
}

# S3 Bucket Names
output "s3_bucket_names" {
  description = "Names of all S3 buckets"
  value = {
    for bucket_key, bucket in module.s3 : bucket_key => bucket.bucket_name
  }
}

output "admin_bucket_name" {
  description = "Name of the admin S3 bucket"
  value = try(module.s3["admin_bucket"].bucket_name, "")
}

output "media_bucket_name" {
  description = "Name of the media S3 bucket"
  value = try(module.s3["media_bucket"].bucket_name, "")
}

# ElastiCache Redis Outputs
output "redis_replication_group_id" {
  description = "ID of the Redis replication group"
  value       = var.create_elasticache ? module.elasticache[0].redis_replication_group_id : ""
}

output "redis_primary_endpoint" {
  description = "Primary endpoint of the Redis cluster"
  value       = var.create_elasticache ? module.elasticache[0].redis_primary_endpoint : ""
}

output "redis_reader_endpoint" {
  description = "Reader endpoint of the Redis cluster"
  value       = var.create_elasticache ? module.elasticache[0].redis_reader_endpoint : ""
}

output "redis_port" {
  description = "Port of the Redis cluster"
  value       = var.create_elasticache ? module.elasticache[0].redis_port : ""
}

# CodePipeline Outputs
