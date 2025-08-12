# ElastiCache Redis Configuration
# Creates Redis cluster for caching

# ElastiCache Redis Module
module "elasticache" {
  count  = var.create_elasticache ? 1 : 0
  source = "../modules/elasticache-redis"

  create_elasticache = true
  project_name       = var.project_name
  env                = var.env
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_id  = module.redis-sg[0].security_group_id

  # Redis configuration
  node_type     = "cache.t3.micro"
  engine_version = "7.0"
  auth_token    = ""  # Leave empty for no auth token
  multi_az      = false  # Set to true for production

  # Alarm actions (SNS topics, etc.)
  alarm_actions = []

  tags = {
    Name        = "${var.project_name}-${var.env}-elasticache"
    Project     = var.project_name
    Service     = "elasticache"
    Environment = var.env
    Terraform   = "true"
  }
} 