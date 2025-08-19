# AWS Cognito Configuration
# Creates User Pool and Identity Pool for authentication

# Cognito Module (Disabled for dev environment)
module "cognito" {
  count  = false ? 1 : 0
  source = "../modules/cognito"

  create_user_pool       = true
  create_user_pool_client = true
  create_identity_pool   = true

  project_name = var.project_name
  env          = var.env

  # User pool configuration
  password_minimum_length    = var.cognito_password_minimum_length
  password_require_lowercase = var.cognito_password_require_lowercase
  password_require_numbers   = var.cognito_password_require_numbers
  password_require_symbols   = var.cognito_password_require_symbols
  password_require_uppercase = var.cognito_password_require_uppercase

  # User pool client configuration
  callback_urls = var.cognito_callback_urls
  logout_urls   = var.cognito_logout_urls

  # Identity pool configuration
  allow_unauthenticated_identities = var.cognito_allow_unauthenticated_identities

  # IAM role policies
  authenticated_role_policy_statements = var.cognito_authenticated_role_policy_statements
  unauthenticated_role_policy_statements = var.cognito_unauthenticated_role_policy_statements

  tags = {
    Name        = "${var.project_name}-${var.env}-cognito"
    Project     = var.project_name
    Service     = "cognito"
    Environment = var.env
    Terraform   = "true"
  }
} 