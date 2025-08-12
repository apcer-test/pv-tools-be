# S3 module outputs 

output "bucket_name" {
  description = "The name of the S3 bucket."
  value       = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  description = "The ARN of the S3 bucket."
  value       = aws_s3_bucket.this.arn
}

output "website_endpoint" {
  description = "The website endpoint of the S3 bucket."
  value       = var.enable_website ? aws_s3_bucket_website_configuration.this[0].website_endpoint : null
} 

output "created_folders" {
  description = "List of general folders created inside the S3 bucket."
  value       = var.folder_paths
}

output "folder_objects" {
  description = "Map of general folder objects created in the S3 bucket."
  value       = aws_s3_object.folders
}

output "created_service_folders" {
  description = "List of service folders created with environment subfolders."
  value       = var.service_folders
}

output "service_folder_objects" {
  description = "Map of service folder objects created in the S3 bucket."
  value       = aws_s3_object.service_folders
}

output "all_service_environment_paths" {
  description = "List of all service environment paths created (e.g., ['admin/qa', 'admin/prod', 'api/qa', 'api/prod'])."
  value       = [for pair in setproduct(var.service_folders, var.environments) : "${pair[0]}/${pair[1]}"]
}

output "created_microservices" {
  description = "List of microservices created under microservices/ folder."
  value       = var.microservices
}

output "microservices_folder_objects" {
  description = "Map of microservices folder objects created in the S3 bucket."
  value       = aws_s3_object.microservices_folders
}

output "all_microservices_environment_paths" {
  description = "List of all microservices environment paths created (e.g., ['microservices/notification-service/qa', 'microservices/notification-service/prod'])."
  value       = [for pair in setproduct(var.microservices, var.environments) : "microservices/${pair[0]}/${pair[1]}"]
}

# OAC Outputs
output "origin_access_control_id" {
  description = "The ID of the Origin Access Control."
  value       = var.enable_oac ? aws_cloudfront_origin_access_control.this[0].id : null
}

output "origin_access_control_etag" {
  description = "The ETag of the Origin Access Control."
  value       = var.enable_oac ? aws_cloudfront_origin_access_control.this[0].etag : null
} 