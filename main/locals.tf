########################################
#           LOCAL VALUES               #
########################################

# Fetch current AWS account ID automatically
data "aws_caller_identity" "current" {}

# Fetch current AWS region
data "aws_region" "current" {}

locals {
  # Automatically fetch AWS account ID
  account_id = data.aws_caller_identity.current.account_id
  
  # Current region
  current_region = data.aws_region.current.id
  
  # Common tags
  common_tags = {
    Project     = var.project_name
    Environment = var.env
    ManagedBy   = "Terraform"
  }
  
  # Pipeline trigger tag pattern
  pipeline_trigger_tag = "${var.project_name}-${var.env}-*"
} 