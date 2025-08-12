# SQS Module Variables

variable "create_queue" {
  description = "Whether to create SQS queue"
  type        = bool
  default     = false
}

variable "create_dead_letter_queue" {
  description = "Whether to create SQS dead letter queue"
  type        = bool
  default     = false
}

variable "queue_name" {
  description = "Name of the SQS queue"
  type        = string
  default     = "queue"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

# Queue attributes
variable "delay_seconds" {
  description = "Delay in seconds before messages become visible"
  type        = number
  default     = 0
}

variable "max_message_size" {
  description = "Maximum message size in bytes"
  type        = number
  default     = 262144
}

variable "message_retention_seconds" {
  description = "Message retention period in seconds"
  type        = number
  default     = 345600
}

variable "receive_wait_time_seconds" {
  description = "Receive wait time in seconds"
  type        = number
  default     = 0
}

variable "visibility_timeout_seconds" {
  description = "Visibility timeout in seconds"
  type        = number
  default     = 30
}

# FIFO queue attributes
variable "fifo_queue" {
  description = "Whether this is a FIFO queue"
  type        = bool
  default     = false
}

variable "content_based_deduplication" {
  description = "Enable content-based deduplication"
  type        = bool
  default     = false
}

variable "deduplication_scope" {
  description = "Deduplication scope"
  type        = string
  default     = "queue"
}

variable "fifo_throughput_limit" {
  description = "FIFO throughput limit"
  type        = string
  default     = "perQueue"
}

# Dead letter queue
variable "redrive_policy" {
  description = "Redrive policy for dead letter queue"
  type        = string
  default     = null
}

# Encryption
variable "sqs_managed_sse_enabled" {
  description = "Enable SQS managed server-side encryption"
  type        = bool
  default     = true
}

variable "kms_master_key_id" {
  description = "KMS master key ID for encryption"
  type        = string
  default     = null
}

# Queue policy
variable "queue_policy" {
  description = "SQS queue policy"
  type        = string
  default     = null
}

# Dead letter queue attributes
variable "dlq_delay_seconds" {
  description = "Delay in seconds for dead letter queue"
  type        = number
  default     = 0
}

variable "dlq_max_message_size" {
  description = "Maximum message size for dead letter queue"
  type        = number
  default     = 262144
}

variable "dlq_message_retention_seconds" {
  description = "Message retention period for dead letter queue"
  type        = number
  default     = 1209600
}

variable "dlq_receive_wait_time_seconds" {
  description = "Receive wait time for dead letter queue"
  type        = number
  default     = 0
}

variable "dlq_visibility_timeout_seconds" {
  description = "Visibility timeout for dead letter queue"
  type        = number
  default     = 30
}

variable "dlq_content_based_deduplication" {
  description = "Content-based deduplication for dead letter queue"
  type        = bool
  default     = false
}

variable "dlq_deduplication_scope" {
  description = "Deduplication scope for dead letter queue"
  type        = string
  default     = "queue"
}

variable "dlq_fifo_throughput_limit" {
  description = "FIFO throughput limit for dead letter queue"
  type        = string
  default     = "perQueue"
}

variable "dlq_queue_policy" {
  description = "SQS queue policy for dead letter queue"
  type        = string
  default     = null
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
} 