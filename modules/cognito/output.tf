# Cognito Module Outputs

output "user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = var.create_user_pool ? aws_cognito_user_pool.main[0].id : null
}

output "user_pool_arn" {
  description = "ARN of the Cognito User Pool"
  value       = var.create_user_pool ? aws_cognito_user_pool.main[0].arn : null
}

output "user_pool_client_id" {
  description = "ID of the Cognito User Pool Client"
  value       = var.create_user_pool_client ? aws_cognito_user_pool_client.main[0].id : null
}

output "user_pool_client_secret" {
  description = "Secret of the Cognito User Pool Client"
  value       = var.create_user_pool_client ? aws_cognito_user_pool_client.main[0].client_secret : null
  sensitive   = true
}

output "identity_pool_id" {
  description = "ID of the Cognito Identity Pool"
  value       = var.create_identity_pool ? aws_cognito_identity_pool.main[0].id : null
}

output "identity_pool_arn" {
  description = "ARN of the Cognito Identity Pool"
  value       = var.create_identity_pool ? aws_cognito_identity_pool.main[0].arn : null
}

output "authenticated_role_arn" {
  description = "ARN of the authenticated IAM role"
  value       = var.create_identity_pool ? aws_iam_role.authenticated[0].arn : null
}

output "unauthenticated_role_arn" {
  description = "ARN of the unauthenticated IAM role"
  value       = var.create_identity_pool ? aws_iam_role.unauthenticated[0].arn : null
} 