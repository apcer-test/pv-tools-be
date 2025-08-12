# AWS Cognito Module
# Creates User Pool and Identity Pool for authentication

# Cognito User Pool
resource "aws_cognito_user_pool" "main" {
  count = var.create_user_pool ? 1 : 0

  name = "${var.project_name}-${var.env}-user-pool"

  # Password policy
  password_policy {
    minimum_length    = var.password_minimum_length
    require_lowercase = var.password_require_lowercase
    require_numbers   = var.password_require_numbers
    require_symbols   = var.password_require_symbols
    require_uppercase = var.password_require_uppercase
    temporary_password_validity_days = var.temporary_password_validity_days
  }

  # Account recovery
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Email configuration
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  # Username attributes
  username_attributes = var.username_attributes

  # Auto verified attributes
  auto_verified_attributes = var.auto_verified_attributes

  # MFA configuration
  mfa_configuration = var.mfa_configuration

  # User pool add-ons
  user_pool_add_ons {
    advanced_security_mode = var.advanced_security_mode
  }

  # Lambda triggers
  dynamic "lambda_config" {
    for_each = var.lambda_triggers != null ? [var.lambda_triggers] : []
    content {
      pre_sign_up         = lambda_config.value.pre_sign_up
      pre_authentication  = lambda_config.value.pre_authentication
      post_authentication = lambda_config.value.post_authentication
      post_confirmation   = lambda_config.value.post_confirmation
      pre_token_generation = lambda_config.value.pre_token_generation
    }
  }

  # Verification message template
  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject       = "Your verification code"
    email_message       = "Your verification code is {####}"
  }



  # Schema attributes
  dynamic "schema" {
    for_each = var.schema_attributes
    content {
      name                = schema.value.name
      attribute_data_type = schema.value.attribute_data_type
      required            = schema.value.required
      mutable             = schema.value.mutable
      string_attribute_constraints {
        min_length = schema.value.string_attribute_constraints.min_length
        max_length = schema.value.string_attribute_constraints.max_length
      }
    }
  }

  tags = merge({
    Name        = "${var.project_name}-${var.env}-user-pool"
    Project     = var.project_name
    Service     = "cognito-user-pool"
    Environment = var.env
    Terraform   = "true"
  }, var.tags)
}

# Cognito User Pool Client
resource "aws_cognito_user_pool_client" "main" {
  count = var.create_user_pool_client ? 1 : 0

  name         = "${var.project_name}-${var.env}-client"
  user_pool_id = aws_cognito_user_pool.main[0].id

  # Client settings
  generate_secret = var.generate_secret
  refresh_token_validity = var.refresh_token_validity

  # Explicit auth flows
  explicit_auth_flows = var.explicit_auth_flows

  # Callback URLs
  callback_urls = var.callback_urls
  logout_urls   = var.logout_urls

  # Allowed OAuth flows
  allowed_oauth_flows                  = var.allowed_oauth_flows
  allowed_oauth_flows_user_pool_client = var.allowed_oauth_flows_user_pool_client
  allowed_oauth_scopes                 = var.allowed_oauth_scopes

  # Supported identity providers
  supported_identity_providers = var.supported_identity_providers

  # Token validity
  access_token_validity  = var.access_token_validity
  id_token_validity      = var.id_token_validity

  # Read and write attributes
  read_attributes  = var.read_attributes
  write_attributes = var.write_attributes
}

# Cognito Identity Pool
resource "aws_cognito_identity_pool" "main" {
  count = var.create_identity_pool ? 1 : 0

  identity_pool_name = "${var.project_name}-${var.env}-identity-pool"

  # Cognito identity providers
  dynamic "cognito_identity_providers" {
    for_each = var.cognito_identity_providers
    content {
      client_id               = cognito_identity_providers.value.client_id
      provider_name           = cognito_identity_providers.value.provider_name
      server_side_token_check = cognito_identity_providers.value.server_side_token_check
    }
  }

  # Allow unauthenticated identities
  allow_unauthenticated_identities = var.allow_unauthenticated_identities

  # OpenID Connect provider ARNs
  openid_connect_provider_arns = var.openid_connect_provider_arns

  # SAML provider ARNs
  saml_provider_arns = var.saml_provider_arns

  # Supported login providers
  supported_login_providers = var.supported_login_providers

  tags = merge({
    Name        = "${var.project_name}-${var.env}-identity-pool"
    Project     = var.project_name
    Service     = "cognito-identity-pool"
    Environment = var.env
    Terraform   = "true"
  }, var.tags)
}

# IAM Role for authenticated users
resource "aws_iam_role" "authenticated" {
  count = var.create_identity_pool ? 1 : 0

  name = "${var.project_name}-${var.env}-cognito-authenticated-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = "cognito-identity.amazonaws.com"
        }
        Condition = {
          StringEquals = {
            "cognito-identity.amazonaws.com:aud" = aws_cognito_identity_pool.main[0].id
          }
          "ForAnyValue:StringLike" = {
            "cognito-identity.amazonaws.com:amr" = "authenticated"
          }
        }
      }
    ]
  })

  tags = merge({
    Name        = "${var.project_name}-${var.env}-cognito-authenticated-role"
    Project     = var.project_name
    Service     = "cognito-iam-role"
    Environment = var.env
    Terraform   = "true"
  }, var.tags)
}

# IAM Role for unauthenticated users
resource "aws_iam_role" "unauthenticated" {
  count = var.create_identity_pool ? 1 : 0

  name = "${var.project_name}-${var.env}-cognito-unauthenticated-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = "cognito-identity.amazonaws.com"
        }
        Condition = {
          StringEquals = {
            "cognito-identity.amazonaws.com:aud" = aws_cognito_identity_pool.main[0].id
          }
          "ForAnyValue:StringLike" = {
            "cognito-identity.amazonaws.com:amr" = "unauthenticated"
          }
        }
      }
    ]
  })

  tags = merge({
    Name        = "${var.project_name}-${var.env}-cognito-unauthenticated-role"
    Project     = var.project_name
    Service     = "cognito-iam-role"
    Environment = var.env
    Terraform   = "true"
  }, var.tags)
}

# IAM Role Policy for authenticated users
resource "aws_iam_role_policy" "authenticated" {
  count = var.create_identity_pool ? 1 : 0

  name = "${var.project_name}-${var.env}-cognito-authenticated-policy"
  role = aws_iam_role.authenticated[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = var.authenticated_role_policy_statements
  })
}

# IAM Role Policy for unauthenticated users
resource "aws_iam_role_policy" "unauthenticated" {
  count = var.create_identity_pool ? 1 : 0

  name = "${var.project_name}-${var.env}-cognito-unauthenticated-policy"
  role = aws_iam_role.unauthenticated[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = var.unauthenticated_role_policy_statements
  })
}

# Identity Pool Role Attachment
resource "aws_cognito_identity_pool_roles_attachment" "main" {
  count = var.create_identity_pool ? 1 : 0

  identity_pool_id = aws_cognito_identity_pool.main[0].id

  roles = {
    authenticated   = aws_iam_role.authenticated[0].arn
    unauthenticated = aws_iam_role.unauthenticated[0].arn
  }
} 