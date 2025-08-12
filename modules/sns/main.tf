# AWS SNS Module
# Creates Simple Notification Service topics and subscriptions

# SNS Topic
resource "aws_sns_topic" "main" {
  count = var.create_topic ? 1 : 0

  name = "${var.project_name}-${var.env}-${var.topic_name}"

  # Topic attributes
  delivery_policy = var.delivery_policy
  policy          = var.topic_policy

  # KMS encryption
  kms_master_key_id = var.kms_master_key_id

  # Content-based deduplication
  fifo_topic                  = var.fifo_topic
  content_based_deduplication = var.content_based_deduplication

  tags = merge({
    Name        = "${var.project_name}-${var.env}-${var.topic_name}"
    Project     = var.project_name
    Service     = "sns-topic"
    Environment = var.env
    Terraform   = "true"
  }, var.tags)
}

# SNS Topic Policy
resource "aws_sns_topic_policy" "main" {
  count = var.create_topic && var.topic_policy != null ? 1 : 0

  arn    = aws_sns_topic.main[0].arn
  policy = var.topic_policy
}

# SNS Topic Subscription
resource "aws_sns_topic_subscription" "main" {
  for_each = var.create_topic ? var.subscriptions : {}

  topic_arn = aws_sns_topic.main[0].arn
  protocol  = each.value.protocol
  endpoint  = each.value.endpoint

  # Subscription attributes
  confirmation_timeout_in_minutes = each.value.confirmation_timeout_in_minutes
  delivery_policy                 = each.value.delivery_policy
  filter_policy                   = each.value.filter_policy
  filter_policy_scope             = each.value.filter_policy_scope
  raw_message_delivery            = each.value.raw_message_delivery
  redrive_policy                  = each.value.redrive_policy

  # FIFO topic specific
  subscription_role_arn = each.value.subscription_role_arn
}

# SNS Platform Application (for mobile push notifications)
resource "aws_sns_platform_application" "main" {
  for_each = var.create_platform_applications ? var.platform_applications : {}

  name                = each.value.name
  platform            = each.value.platform
  platform_credential = each.value.platform_credential
  platform_principal  = each.value.platform_principal

  # Application attributes
  event_delivery_failure_topic_arn = each.value.event_delivery_failure_topic_arn
  event_endpoint_created_topic_arn = each.value.event_endpoint_created_topic_arn
  event_endpoint_deleted_topic_arn = each.value.event_endpoint_deleted_topic_arn
  event_endpoint_updated_topic_arn = each.value.event_endpoint_updated_topic_arn
  failure_feedback_role_arn        = each.value.failure_feedback_role_arn
  success_feedback_role_arn        = each.value.success_feedback_role_arn
  success_feedback_sample_rate     = each.value.success_feedback_sample_rate
}

# SNS Platform Endpoint (for mobile push notifications)
resource "aws_sns_platform_endpoint" "main" {
  for_each = var.create_platform_endpoints ? var.platform_endpoints : {}

  platform_application_arn = each.value.platform_application_arn
  token                   = each.value.token
  custom_user_data        = each.value.custom_user_data

  # Endpoint attributes
  enabled = each.value.enabled
}

# SNS Topic Data Protection Policy
resource "aws_sns_topic_data_protection_policy" "main" {
  count = var.create_topic && var.data_protection_policy != null ? 1 : 0

  arn    = aws_sns_topic.main[0].arn
  policy = var.data_protection_policy
} 