output "vault_arn" {
  description = "ARN of the AWS Backup vault"
  value       = aws_backup_vault.main.arn
}

output "vault_name" {
  description = "Name of the AWS Backup vault"
  value       = aws_backup_vault.main.name
}

output "plan_name" {
  description = "Name of the AWS Backup plan"
  value       = aws_backup_plan.main.name
}

output "selection_name" {
  description = "Name of the AWS Backup selection"
  value       = aws_backup_selection.main.name
} 