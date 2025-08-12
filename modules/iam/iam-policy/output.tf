# IAM Policy Module Outputs

output "policy_arn" {
  description = "ARN of the IAM policy"
  value       = var.create_iam_policy ? aws_iam_policy.iam_policy[0].arn : null
}