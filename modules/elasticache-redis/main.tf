# ElastiCache Redis Module
# Creates Redis cluster for caching

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0.0"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

##########################################################
# ElastiCache Subnet Group
##########################################################
resource "aws_elasticache_subnet_group" "redis" {
  count      = var.create_elasticache ? 1 : 0
  name       = "${var.project_name}-${var.env}-redis-subnet-group"
  subnet_ids = var.subnet_ids

  tags = merge(
    {
      Name        = "${var.project_name}-${var.env}-redis-subnet-group"
      Project     = var.project_name
      Service     = "elasticache-subnet-group"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
}

##########################################################
# ElastiCache Parameter Group
##########################################################
resource "aws_elasticache_parameter_group" "redis" {
  count  = var.create_elasticache ? 1 : 0
  family = "redis7"
  name   = "${var.project_name}-${var.env}-redis-params"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "notify-keyspace-events"
    value = "Ex"
  }

  tags = merge(
    {
      Name        = "${var.project_name}-${var.env}-redis-params"
      Project     = var.project_name
      Service     = "elasticache-parameter-group"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
}

##########################################################
# ElastiCache Replication Group (Redis Cluster)
##########################################################
resource "aws_elasticache_replication_group" "redis" {
  count = var.create_elasticache ? 1 : 0

  replication_group_id = "${var.project_name}-${var.env}-redis"
  description         = "Redis cluster for ${var.project_name} ${var.env}"
  node_type           = var.node_type
  port                = 6379
  parameter_group_name = aws_elasticache_parameter_group.redis[0].name
  subnet_group_name   = aws_elasticache_subnet_group.redis[0].name
  security_group_ids  = [var.security_group_id]
  engine              = "redis"
  engine_version      = var.engine_version
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  # Only set auth_token if provided
  auth_token = var.auth_token != "" ? var.auth_token : null

  # Multi-AZ configuration
  automatic_failover_enabled = var.multi_az
  num_cache_clusters         = var.multi_az ? 2 : 1

  # Logging configuration
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_logs[0].name
    destination_type = "cloudwatch-logs"
    log_format       = "text"
    log_type         = "slow-log"
  }

  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_logs[0].name
    destination_type = "cloudwatch-logs"
    log_format       = "text"
    log_type         = "engine-log"
  }

  tags = merge(
    {
      Name        = "${var.project_name}-${var.env}-redis"
      Project     = var.project_name
      Service     = "elasticache-redis"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
}

##########################################################
# CloudWatch Log Group for Redis Logs
##########################################################
resource "aws_cloudwatch_log_group" "redis_logs" {
  count             = var.create_elasticache ? 1 : 0
  name              = "/aws/elasticache/${var.project_name}-${var.env}-redis"
  retention_in_days = 7

  tags = merge(
    {
      Name        = "${var.project_name}-${var.env}-redis-logs"
      Project     = var.project_name
      Service     = "elasticache-logs"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
}

##########################################################
# CloudWatch Alarms for Redis
##########################################################
resource "aws_cloudwatch_metric_alarm" "redis_cpu" {
  count = var.create_elasticache ? 1 : 0

  alarm_name          = "${var.project_name}-${var.env}-redis-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Redis CPU utilization is high"
  alarm_actions       = var.alarm_actions

  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.redis[0].id
  }

  tags = merge(
    {
      Name        = "${var.project_name}-${var.env}-redis-cpu-alarm"
      Project     = var.project_name
      Service     = "elasticache-alarm"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
}

resource "aws_cloudwatch_metric_alarm" "redis_memory" {
  count = var.create_elasticache ? 1 : 0

  alarm_name          = "${var.project_name}-${var.env}-redis-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "Redis memory usage is high"
  alarm_actions       = var.alarm_actions

  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.redis[0].id
  }

  tags = merge(
    {
      Name        = "${var.project_name}-${var.env}-redis-memory-alarm"
      Project     = var.project_name
      Service     = "elasticache-alarm"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
}

resource "aws_cloudwatch_metric_alarm" "redis_connections" {
  count = var.create_elasticache ? 1 : 0

  alarm_name          = "${var.project_name}-${var.env}-redis-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CurrConnections"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "1000"
  alarm_description   = "Redis connection count is high"
  alarm_actions       = var.alarm_actions

  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.redis[0].id
  }

  tags = merge(
    {
      Name        = "${var.project_name}-${var.env}-redis-connections-alarm"
      Project     = var.project_name
      Service     = "elasticache-alarm"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
} 