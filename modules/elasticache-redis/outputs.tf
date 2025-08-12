# ElastiCache Redis Module Outputs

output "redis_replication_group_id" {
  description = "ID of the Redis replication group"
  value       = var.create_elasticache ? aws_elasticache_replication_group.redis[0].id : ""
}

output "redis_replication_group_arn" {
  description = "ARN of the Redis replication group"
  value       = var.create_elasticache ? aws_elasticache_replication_group.redis[0].arn : ""
}

output "redis_primary_endpoint" {
  description = "Primary endpoint of the Redis cluster"
  value       = var.create_elasticache ? aws_elasticache_replication_group.redis[0].primary_endpoint_address : ""
}

output "redis_reader_endpoint" {
  description = "Reader endpoint of the Redis cluster"
  value       = var.create_elasticache ? aws_elasticache_replication_group.redis[0].reader_endpoint_address : ""
}

output "redis_port" {
  description = "Port of the Redis cluster"
  value       = var.create_elasticache ? aws_elasticache_replication_group.redis[0].port : ""
}

output "redis_subnet_group_name" {
  description = "Name of the Redis subnet group"
  value       = var.create_elasticache ? aws_elasticache_subnet_group.redis[0].name : ""
}

output "redis_parameter_group_name" {
  description = "Name of the Redis parameter group"
  value       = var.create_elasticache ? aws_elasticache_parameter_group.redis[0].name : ""
}

output "redis_log_group_name" {
  description = "Name of the CloudWatch log group for Redis"
  value       = var.create_elasticache ? aws_cloudwatch_log_group.redis_logs[0].name : ""
} 