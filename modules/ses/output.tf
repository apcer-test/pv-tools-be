# SES Module Outputs

output "domain_identity_arn" {
  description = "ARN of the SES domain identity"
  value       = var.create_domain_identity ? aws_ses_domain_identity.main[0].arn : null
}

output "domain_identity_verification_token" {
  description = "Verification token for the SES domain identity"
  value       = var.create_domain_identity ? aws_ses_domain_identity.main[0].verification_token : null
}

output "domain_dkim_tokens" {
  description = "DKIM tokens for the SES domain"
  value       = var.create_domain_identity ? aws_ses_domain_dkim.main[0].dkim_tokens : null
}

output "mail_from_domain" {
  description = "Mail from domain for SES"
  value       = var.create_domain_identity ? aws_ses_domain_mail_from.main[0].mail_from_domain : null
}

output "configuration_set_name" {
  description = "Name of the SES configuration set"
  value       = var.create_configuration_set ? aws_ses_configuration_set.main[0].name : null
}

output "receipt_rule_set_name" {
  description = "Name of the SES receipt rule set"
  value       = var.create_receipt_rule_set ? aws_ses_receipt_rule_set.main[0].rule_set_name : null
} 