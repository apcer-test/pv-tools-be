# SQS Module Outputs

output "queue_url" {
  description = "URL of the SQS queue"
  value       = var.create_queue ? aws_sqs_queue.main[0].url : null
}

output "queue_arn" {
  description = "ARN of the SQS queue"
  value       = var.create_queue ? aws_sqs_queue.main[0].arn : null
}

output "queue_name" {
  description = "Name of the SQS queue"
  value       = var.create_queue ? aws_sqs_queue.main[0].name : null
}

output "dead_letter_queue_url" {
  description = "URL of the SQS dead letter queue"
  value       = var.create_dead_letter_queue ? aws_sqs_queue.dead_letter[0].url : null
}

output "dead_letter_queue_arn" {
  description = "ARN of the SQS dead letter queue"
  value       = var.create_dead_letter_queue ? aws_sqs_queue.dead_letter[0].arn : null
}

output "dead_letter_queue_name" {
  description = "Name of the SQS dead letter queue"
  value       = var.create_dead_letter_queue ? aws_sqs_queue.dead_letter[0].name : null
} 