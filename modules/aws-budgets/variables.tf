# AWS Budgets Module Variables

variable "create_budget" {
  description = "Whether to create AWS Budget"
  type        = bool
  default     = false
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "env" {
  description = "Environment name"
  type        = string
}

variable "budget_type" {
  description = "Type of budget (COST, USAGE, RI_UTILIZATION, RI_COVERAGE, SAVINGS_PLANS_UTILIZATION, SAVINGS_PLANS_COVERAGE)"
  type        = string
  default     = "COST"
  validation {
    condition = contains([
      "COST", "USAGE", "RI_UTILIZATION", "RI_COVERAGE", 
      "SAVINGS_PLANS_UTILIZATION", "SAVINGS_PLANS_COVERAGE"
    ], var.budget_type)
    error_message = "Budget type must be one of: COST, USAGE, RI_UTILIZATION, RI_COVERAGE, SAVINGS_PLANS_UTILIZATION, SAVINGS_PLANS_COVERAGE."
  }
}

variable "budget_limit_amount" {
  description = "Budget limit amount"
  type        = string
  default     = "100"
}

variable "budget_limit_unit" {
  description = "Budget limit unit (USD, EUR, etc.)"
  type        = string
  default     = "USD"
}

variable "budget_time_period_start" {
  description = "Budget time period start (YYYY-MM-DD_HH:MM:SS)"
  type        = string
  default     = null
}

variable "budget_time_period_end" {
  description = "Budget time period end (YYYY-MM-DD_HH:MM:SS)"
  type        = string
  default     = null
}

variable "budget_time_unit" {
  description = "Budget time unit (MONTHLY, QUARTERLY, ANNUALLY)"
  type        = string
  default     = "MONTHLY"
  validation {
    condition = contains(["MONTHLY", "QUARTERLY", "ANNUALLY"], var.budget_time_unit)
    error_message = "Budget time unit must be one of: MONTHLY, QUARTERLY, ANNUALLY."
  }
}

variable "cost_filters" {
  description = "Cost filters to scope the budget"
  type        = map(list(string))
  default     = {}
}

variable "budget_notifications" {
  description = "List of budget notifications"
  type = list(object({
    comparison_operator        = string
    threshold                  = number
    threshold_type             = string
    notification_type          = string
    subscriber_email_addresses = list(string)
    subscriber_sns_topic_arns  = optional(list(string), [])
  }))
  default = []
  validation {
    condition = alltrue([
      for notification in var.budget_notifications : 
      contains(["GREATER_THAN", "LESS_THAN", "EQUAL_TO"], notification.comparison_operator)
    ])
    error_message = "Comparison operator must be one of: GREATER_THAN, LESS_THAN, EQUAL_TO."
  }
  validation {
    condition = alltrue([
      for notification in var.budget_notifications : 
      contains(["PERCENTAGE", "ABSOLUTE_VALUE"], notification.threshold_type)
    ])
    error_message = "Threshold type must be one of: PERCENTAGE, ABSOLUTE_VALUE."
  }
  validation {
    condition = alltrue([
      for notification in var.budget_notifications : 
      contains(["ACTUAL", "FORECASTED"], notification.notification_type)
    ])
    error_message = "Notification type must be one of: ACTUAL, FORECASTED."
  }
}

variable "create_budget_alarm" {
  description = "Whether to create CloudWatch alarm for budget threshold"
  type        = bool
  default     = true
}

variable "alarm_evaluation_periods" {
  description = "Number of evaluation periods for CloudWatch alarm"
  type        = number
  default     = 1
}

variable "alarm_period" {
  description = "Period in seconds for CloudWatch alarm"
  type        = number
  default     = 86400  # 24 hours
}

variable "alarm_actions" {
  description = "List of ARNs for alarm actions"
  type        = list(string)
  default     = []
}

variable "ok_actions" {
  description = "List of ARNs for OK actions"
  type        = list(string)
  default     = []
}

variable "create_sns_topic" {
  description = "Whether to create SNS topic for budget notifications"
  type        = bool
  default     = true
}

variable "subscriber_email_addresses" {
  description = "List of email addresses to subscribe to budget notifications"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
} 