# IAM Role Module Outputs

# IAM Role
output "iam_role_arn" {
  description = "ARN of IAM role"
  value       = var.create_iam_role ? aws_iam_role.iam_role[0].arn : null
}

output "iam_role_name" {
  description = "Name of IAM role"
  value       = var.create_iam_role ? aws_iam_role.iam_role[0].name : null
}

# Policy Attachments (for debugging)
output "attached_policy_arns" {
  description = "List of all policy ARNs attached to the role"
  value       = var.create_iam_role ? local.all_policy_arns : []
}

output "managed_policy_count" {
  description = "Number of AWS managed policies attached"
  value       = var.create_iam_role ? length(var.custom_role_policy_arns) : 0
}

output "custom_policy_count" {
  description = "Number of custom policies attached"
  value       = var.create_iam_role ? length(var.additional_policy_arns) : 0
}