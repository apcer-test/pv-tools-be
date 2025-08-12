# AWS SES Module
# Creates Simple Email Service configuration

# SES Domain Identity
resource "aws_ses_domain_identity" "main" {
  count = var.create_domain_identity ? 1 : 0

  domain = var.domain_name
}

# SES Domain DKIM
resource "aws_ses_domain_dkim" "main" {
  count = var.create_domain_identity ? 1 : 0

  domain = aws_ses_domain_identity.main[0].domain
}

# SES Domain Mail From
resource "aws_ses_domain_mail_from" "main" {
  count = var.create_domain_identity ? 1 : 0

  domain           = aws_ses_domain_identity.main[0].domain
  mail_from_domain = "mail.${aws_ses_domain_identity.main[0].domain}"
}

# Route53 MX record for SES
resource "aws_route53_record" "ses_mx" {
  count = var.create_domain_identity && var.route53_zone_id != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = aws_ses_domain_mail_from.main[0].mail_from_domain
  type    = "MX"
  ttl     = "600"
  records = ["10 feedback-smtp.${var.region}.amazonses.com"]
}

# Route53 TXT record for SES
resource "aws_route53_record" "ses_txt" {
  count = var.create_domain_identity && var.route53_zone_id != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = aws_ses_domain_mail_from.main[0].mail_from_domain
  type    = "TXT"
  ttl     = "600"
  records = ["v=spf1 include:amazonses.com ~all"]
}

# Route53 DKIM records
resource "aws_route53_record" "ses_dkim" {
  count = var.create_domain_identity && var.route53_zone_id != "" ? length(aws_ses_domain_dkim.main[0].dkim_tokens) : 0

  zone_id = var.route53_zone_id
  name    = "${element(aws_ses_domain_dkim.main[0].dkim_tokens, count.index)}._domainkey.${aws_ses_domain_identity.main[0].domain}"
  type    = "CNAME"
  ttl     = "600"
  records = ["${element(aws_ses_domain_dkim.main[0].dkim_tokens, count.index)}.dkim.amazonses.com"]
}

# SES Email Identity
resource "aws_ses_email_identity" "main" {
  for_each = var.create_email_identities ? toset(var.email_identities) : []

  email = each.value
}

# SES Configuration Set
resource "aws_ses_configuration_set" "main" {
  count = var.create_configuration_set ? 1 : 0

  name = "${var.project_name}-${var.env}-ses-config"

  # Delivery options
  dynamic "delivery_options" {
    for_each = var.delivery_options != null ? [var.delivery_options] : []
    content {
      tls_policy = delivery_options.value.tls_policy
    }
  }

  # Reputation metrics
  reputation_metrics_enabled = var.reputation_metrics_enabled

  # Sending enabled
  sending_enabled = var.sending_enabled
}

# SES Configuration Set Event Destination
resource "aws_ses_configuration_set_event_destination" "main" {
  for_each = var.create_configuration_set ? var.event_destinations : {}

  configuration_set_name = aws_ses_configuration_set.main[0].name
  event_destination_name = each.key

  # CloudWatch destination
  dynamic "cloudwatch_destination" {
    for_each = each.value.cloudwatch_destination != null ? [each.value.cloudwatch_destination] : []
    content {
      default_value  = cloudwatch_destination.value.default_value
      dimension_name = cloudwatch_destination.value.dimension_name
      value_source   = cloudwatch_destination.value.value_source
    }
  }

  # Kinesis destination
  dynamic "kinesis_destination" {
    for_each = each.value.kinesis_destination != null ? [each.value.kinesis_destination] : []
    content {
      role_arn   = kinesis_destination.value.role_arn
      stream_arn = kinesis_destination.value.stream_arn
    }
  }

  # SNS destination
  dynamic "sns_destination" {
    for_each = each.value.sns_destination != null ? [each.value.sns_destination] : []
    content {
      topic_arn = sns_destination.value.topic_arn
    }
  }

  # Event types
  matching_event_types = each.value.matching_event_types
}

# SES Receipt Rule Set
resource "aws_ses_receipt_rule_set" "main" {
  count = var.create_receipt_rule_set ? 1 : 0

  rule_set_name = "${var.project_name}-${var.env}-receipt-rules"
}

# SES Receipt Rules
resource "aws_ses_receipt_rule" "main" {
  for_each = var.create_receipt_rule_set ? var.receipt_rules : {}

  name          = each.key
  rule_set_name = aws_ses_receipt_rule_set.main[0].rule_set_name
  recipients    = each.value.recipients
  enabled       = each.value.enabled
  scan_enabled  = each.value.scan_enabled
  tls_policy    = each.value.tls_policy

  # S3 action
  dynamic "s3_action" {
    for_each = each.value.s3_action != null ? [each.value.s3_action] : []
    content {
      position         = s3_action.value.position
      bucket_name      = s3_action.value.bucket_name
      object_key_prefix = s3_action.value.object_key_prefix
      topic_arn        = s3_action.value.topic_arn
    }
  }

  # SNS action
  dynamic "sns_action" {
    for_each = each.value.sns_action != null ? [each.value.sns_action] : []
    content {
      position = sns_action.value.position
      topic_arn = sns_action.value.topic_arn
    }
  }

  # Lambda action
  dynamic "lambda_action" {
    for_each = each.value.lambda_action != null ? [each.value.lambda_action] : []
    content {
      position       = lambda_action.value.position
      function_arn   = lambda_action.value.function_arn
      invocation_type = lambda_action.value.invocation_type
    }
  }

  # Bounce action
  dynamic "bounce_action" {
    for_each = each.value.bounce_action != null ? [each.value.bounce_action] : []
    content {
      position        = bounce_action.value.position
      message         = bounce_action.value.message
      sender          = bounce_action.value.sender
      smtp_reply_code = bounce_action.value.smtp_reply_code
      status_code     = bounce_action.value.status_code
      topic_arn       = bounce_action.value.topic_arn
    }
  }

  # Stop action
  dynamic "stop_action" {
    for_each = each.value.stop_action != null ? [each.value.stop_action] : []
    content {
      position  = stop_action.value.position
      scope     = stop_action.value.scope
      topic_arn = stop_action.value.topic_arn
    }
  }

  # Add header action
  dynamic "add_header_action" {
    for_each = each.value.add_header_action != null ? [each.value.add_header_action] : []
    content {
      position     = add_header_action.value.position
      header_name  = add_header_action.value.header_name
      header_value = add_header_action.value.header_value
    }
  }

  # Workmail action
  dynamic "workmail_action" {
    for_each = each.value.workmail_action != null ? [each.value.workmail_action] : []
    content {
      position        = workmail_action.value.position
      organization_arn = workmail_action.value.organization_arn
      topic_arn       = workmail_action.value.topic_arn
    }
  }
} 