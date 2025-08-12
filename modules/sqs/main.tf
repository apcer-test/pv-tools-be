# AWS SQS Module
# Creates Simple Queue Service queues

# SQS Queue
resource "aws_sqs_queue" "main" {
  count = var.create_queue ? 1 : 0

  name = "${var.project_name}-${var.env}-${var.queue_name}"

  # Queue attributes
  delay_seconds                  = var.delay_seconds
  max_message_size              = var.max_message_size
  message_retention_seconds     = var.message_retention_seconds
  receive_wait_time_seconds     = var.receive_wait_time_seconds
  visibility_timeout_seconds    = var.visibility_timeout_seconds

  # FIFO queue attributes
  fifo_queue                    = var.fifo_queue
  content_based_deduplication   = var.content_based_deduplication
  deduplication_scope           = var.deduplication_scope
  fifo_throughput_limit         = var.fifo_throughput_limit

  # Dead letter queue
  redrive_policy = var.redrive_policy

  # Encryption
  sqs_managed_sse_enabled = var.sqs_managed_sse_enabled
  kms_master_key_id       = var.kms_master_key_id

  # Tags
  tags = merge({
    Name        = "${var.project_name}-${var.env}-${var.queue_name}"
    Project     = var.project_name
    Service     = "sqs-queue"
    Environment = var.env
    Terraform   = "true"
  }, var.tags)
}

# SQS Queue Policy
resource "aws_sqs_queue_policy" "main" {
  count = var.create_queue && var.queue_policy != null ? 1 : 0

  queue_url = aws_sqs_queue.main[0].url
  policy    = var.queue_policy
}

# Dead Letter Queue
resource "aws_sqs_queue" "dead_letter" {
  count = var.create_dead_letter_queue ? 1 : 0

  name = "${var.project_name}-${var.env}-${var.queue_name}-dlq"

  # Queue attributes
  delay_seconds                  = var.dlq_delay_seconds
  max_message_size              = var.dlq_max_message_size
  message_retention_seconds     = var.dlq_message_retention_seconds
  receive_wait_time_seconds     = var.dlq_receive_wait_time_seconds
  visibility_timeout_seconds    = var.dlq_visibility_timeout_seconds

  # FIFO queue attributes
  fifo_queue                    = var.fifo_queue
  content_based_deduplication   = var.dlq_content_based_deduplication
  deduplication_scope           = var.dlq_deduplication_scope
  fifo_throughput_limit         = var.dlq_fifo_throughput_limit

  # Encryption
  sqs_managed_sse_enabled = var.sqs_managed_sse_enabled
  kms_master_key_id       = var.kms_master_key_id

  tags = merge({
    Name        = "${var.project_name}-${var.env}-${var.queue_name}-dlq"
    Project     = var.project_name
    Service     = "sqs-dead-letter-queue"
    Environment = var.env
    Terraform   = "true"
  }, var.tags)
}

# SQS Queue Policy for Dead Letter Queue
resource "aws_sqs_queue_policy" "dead_letter" {
  count = var.create_dead_letter_queue && var.dlq_queue_policy != null ? 1 : 0

  queue_url = aws_sqs_queue.dead_letter[0].url
  policy    = var.dlq_queue_policy
} 