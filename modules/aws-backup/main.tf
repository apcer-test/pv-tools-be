# AWS Backup Module for Disaster Recovery

resource "aws_backup_vault" "main" {
  name        = var.vault_name
  kms_key_arn = var.kms_key_arn
  tags        = var.tags
}

resource "aws_backup_plan" "main" {
  name = var.plan_name

  rule {
    rule_name         = var.rule_name
    target_vault_name = aws_backup_vault.main.name
    schedule          = var.schedule
    start_window      = var.start_window
    completion_window = var.completion_window
    
    lifecycle {
      delete_after = var.delete_after_days != null ? var.delete_after_days : var.retention_days
      cold_storage_after = var.cold_storage_after_days
    }
    
    recovery_point_tags = var.recovery_point_tags
  }

  # Additional lifecycle rule for long-term retention
  dynamic "rule" {
    for_each = var.enable_long_term_retention ? [1] : []
    content {
      rule_name         = "${var.rule_name}-long-term"
      target_vault_name = aws_backup_vault.main.name
      schedule          = var.long_term_schedule
      start_window      = var.start_window
      completion_window = var.completion_window
      
      lifecycle {
        delete_after = var.long_term_retention_days
        cold_storage_after = var.long_term_cold_storage_after_days
      }
      
      recovery_point_tags = merge(var.recovery_point_tags, {
        RetentionType = "long-term"
      })
    }
  }
}

resource "aws_iam_role" "backup" {
  name = "${var.project_name}-backup-role-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "backup.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "backup" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_backup_selection" "main" {
  iam_role_arn = aws_iam_role.backup.arn
  name         = var.selection_name
  plan_id      = aws_backup_plan.main.id

  resources = var.resource_arns

  selection_tag {
    type  = "STRINGEQUALS"
    key   = var.selection_tag_key
    value = var.selection_tag_value
  }
} 