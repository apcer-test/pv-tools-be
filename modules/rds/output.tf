# RDS module outputs 

output "db_instance_identifier" {
  description = "The RDS instance identifier."
  value       = aws_db_instance.this.id
}

output "db_instance_arn" {
  description = "The ARN of the RDS instance."
  value       = aws_db_instance.this.arn
}

output "db_instance_endpoint" {
  description = "The connection endpoint."
  value       = aws_db_instance.this.endpoint
}

output "db_instance_address" {
  description = "The address of the RDS instance."
  value       = aws_db_instance.this.address
}

output "master_user_secret_arn" {
  description = "The ARN of the master user secret managed by AWS."
  value       = aws_db_instance.this.master_user_secret[0].secret_arn
}