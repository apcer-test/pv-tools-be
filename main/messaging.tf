# AWS Messaging Services Configuration
# Creates SES, SNS, and SQS resources

# SES Module
# module "ses" {
#   count  = var.create_ses ? 1 : 0
#   source = "../modules/ses"

#   create_domain_identity = true
#   create_configuration_set = true
#   create_receipt_rule_set = true

#   domain_name = var.ses_domain_name
#   route53_zone_id = var.route53_zone_id
#   region = var.region
#   project_name = var.project_name
#   env = var.env

#   # Configuration set
#   reputation_metrics_enabled = var.ses_reputation_metrics_enabled
#   sending_enabled = var.ses_sending_enabled

#   # Event destinations
#   event_destinations = var.ses_event_destinations

#   # Receipt rules
#   receipt_rules = var.ses_receipt_rules

#   tags = {
#     Name        = "${var.project_name}-${var.env}-ses"
#     Project     = var.project_name
#     Service     = "ses"
#     Environment = var.env
#     Terraform   = "true"
#   }
# }

# SNS Module
# module "sns" {
#   count  = var.create_sns ? 1 : 0
#   source = "../modules/sns"

#   create_topic = true
#   topic_name = var.sns_topic_name
#   project_name = var.project_name
#   env = var.env

#   # Topic configuration
#   fifo_topic = var.sns_fifo_topic
#   content_based_deduplication = var.sns_content_based_deduplication
#   kms_master_key_id = var.sns_kms_master_key_id

#   # Subscriptions
#   subscriptions = var.sns_subscriptions

#   tags = {
#     Name        = "${var.project_name}-${var.env}-sns"
#     Project     = var.project_name
#     Service     = "sns"
#     Environment = var.env
#     Terraform   = "true"
#   }
# }

# SQS Module
# module "sqs" {
#   count  = var.create_sqs ? 1 : 0
#   source = "../modules/sqs"

#   create_queue = true
#   create_dead_letter_queue = var.sqs_create_dead_letter_queue
#   queue_name = var.sqs_queue_name
#   project_name = var.project_name
#   env = var.env

#   # Queue configuration
#   delay_seconds = var.sqs_delay_seconds
#   max_message_size = var.sqs_max_message_size
#   message_retention_seconds = var.sqs_message_retention_seconds
#   receive_wait_time_seconds = var.sqs_receive_wait_time_seconds
#   visibility_timeout_seconds = var.sqs_visibility_timeout_seconds

#   # FIFO configuration
#   fifo_queue = var.sqs_fifo_queue
#   content_based_deduplication = var.sqs_content_based_deduplication

#   # Encryption
#   sqs_managed_sse_enabled = var.sqs_managed_sse_enabled
#   kms_master_key_id = var.sqs_kms_master_key_id

#   # Dead letter queue configuration
#   redrive_policy = var.sqs_redrive_policy

#   tags = {
#     Name        = "${var.project_name}-${var.env}-sqs"
#     Project     = var.project_name
#     Service     = "sqs"
#     Environment = var.env
#     Terraform   = "true"
#   }
# } 