# Cognito Module Variables

variable "create_user_pool" {
  description = "Whether to create Cognito User Pool"
  type        = bool
  default     = false
}

variable "create_user_pool_client" {
  description = "Whether to create Cognito User Pool Client"
  type        = bool
  default     = false
}

variable "create_identity_pool" {
  description = "Whether to create Cognito Identity Pool"
  type        = bool
  default     = false
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

# Password policy variables
variable "password_minimum_length" {
  description = "Minimum password length"
  type        = number
  default     = 8
}

variable "password_require_lowercase" {
  description = "Require lowercase in password"
  type        = bool
  default     = true
}

variable "password_require_numbers" {
  description = "Require numbers in password"
  type        = bool
  default     = true
}

variable "password_require_symbols" {
  description = "Require symbols in password"
  type        = bool
  default     = true
}

variable "password_require_uppercase" {
  description = "Require uppercase in password"
  type        = bool
  default     = true
}

variable "temporary_password_validity_days" {
  description = "Temporary password validity in days"
  type        = number
  default     = 7
}

# User pool configuration
variable "username_attributes" {
  description = "Username attributes"
  type        = list(string)
  default     = ["email"]
}

variable "auto_verified_attributes" {
  description = "Auto verified attributes"
  type        = list(string)
  default     = ["email"]
}

variable "mfa_configuration" {
  description = "MFA configuration"
  type        = string
  default     = "OFF"
}

variable "advanced_security_mode" {
  description = "Advanced security mode"
  type        = string
  default     = "OFF"
}

# Lambda triggers
variable "lambda_triggers" {
  description = "Lambda triggers configuration"
  type = object({
    pre_sign_up         = optional(string)
    pre_authentication  = optional(string)
    post_authentication = optional(string)
    post_confirmation   = optional(string)
    pre_token_generation = optional(string)
  })
  default = null
}

# Schema attributes
variable "schema_attributes" {
  description = "User pool schema attributes"
  type = list(object({
    name                = string
    attribute_data_type = string
    required            = bool
    mutable             = bool
    string_attribute_constraints = object({
      min_length = number
      max_length = number
    })
  }))
  default = []
}

# User pool client configuration
variable "generate_secret" {
  description = "Generate client secret"
  type        = bool
  default     = false
}

variable "refresh_token_validity" {
  description = "Refresh token validity in days"
  type        = number
  default     = 30
}

variable "explicit_auth_flows" {
  description = "Explicit auth flows"
  type        = list(string)
  default     = ["ALLOW_USER_PASSWORD_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
}

variable "callback_urls" {
  description = "Callback URLs"
  type        = list(string)
  default     = []
}

variable "logout_urls" {
  description = "Logout URLs"
  type        = list(string)
  default     = []
}

variable "allowed_oauth_flows" {
  description = "Allowed OAuth flows"
  type        = list(string)
  default     = []
}

variable "allowed_oauth_flows_user_pool_client" {
  description = "Allowed OAuth flows for user pool client"
  type        = bool
  default     = false
}

variable "allowed_oauth_scopes" {
  description = "Allowed OAuth scopes"
  type        = list(string)
  default     = []
}

variable "supported_identity_providers" {
  description = "Supported identity providers"
  type        = list(string)
  default     = ["COGNITO"]
}

variable "access_token_validity" {
  description = "Access token validity in hours"
  type        = number
  default     = 1
}

variable "id_token_validity" {
  description = "ID token validity in hours"
  type        = number
  default     = 1
}

variable "read_attributes" {
  description = "Read attributes"
  type        = list(string)
  default     = ["email", "email_verified"]
}

variable "write_attributes" {
  description = "Write attributes"
  type        = list(string)
  default     = ["email"]
}

# Identity pool configuration
variable "cognito_identity_providers" {
  description = "Cognito identity providers"
  type = list(object({
    client_id               = string
    provider_name           = string
    server_side_token_check = bool
  }))
  default = []
}

variable "allow_unauthenticated_identities" {
  description = "Allow unauthenticated identities"
  type        = bool
  default     = false
}

variable "developer_provider_name" {
  description = "Developer provider name"
  type        = string
  default     = ""
}

variable "openid_connect_provider_arns" {
  description = "OpenID Connect provider ARNs"
  type        = list(string)
  default     = []
}

variable "saml_provider_arns" {
  description = "SAML provider ARNs"
  type        = list(string)
  default     = []
}

variable "supported_login_providers" {
  description = "Supported login providers"
  type        = map(string)
  default     = {}
}

# IAM role policies
variable "authenticated_role_policy_statements" {
  description = "IAM policy statements for authenticated users"
  type        = list(any)
  default     = []
}

variable "unauthenticated_role_policy_statements" {
  description = "IAM policy statements for unauthenticated users"
  type        = list(any)
  default     = []
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
} 