# CloudWatch Synthetics Module
# Creates synthetic monitoring canaries for endpoint health checks

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0.0"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

##########################################################
# IAM Role for Synthetics Canary
##########################################################
resource "aws_iam_role" "synthetics_role" {
  count = var.create_synthetics ? 1 : 0
  name  = "${var.project_name}-${var.env}-synthetics-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(
    {
      Name        = "${var.project_name}-${var.env}-synthetics-role"
      Project     = var.project_name
      Service     = "synthetics-role"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "synthetics_basic" {
  count      = var.create_synthetics ? 1 : 0
  role       = aws_iam_role.synthetics_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom policy for Synthetics
resource "aws_iam_role_policy" "synthetics_policy" {
  count = var.create_synthetics ? 1 : 0
  name  = "${var.project_name}-${var.env}-synthetics-policy"
  role  = aws_iam_role.synthetics_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.synthetics_artifacts[0].arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.synthetics_artifacts[0].arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:AssignPrivateIpAddresses",
          "ec2:UnassignPrivateIpAddresses"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

##########################################################
# S3 Bucket for Canary Artifacts
##########################################################
resource "aws_s3_bucket" "synthetics_artifacts" {
  count  = var.create_synthetics ? 1 : 0
  bucket = "${var.project_name}-${var.env}-synthetics-artifacts"

  tags = merge(
    {
      Name        = "${var.project_name}-${var.env}-synthetics-artifacts"
      Project     = var.project_name
      Service     = "synthetics-artifacts"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
}

resource "aws_s3_bucket_versioning" "synthetics_artifacts" {
  count  = var.create_synthetics ? 1 : 0
  bucket = aws_s3_bucket.synthetics_artifacts[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "synthetics_artifacts" {
  count  = var.create_synthetics ? 1 : 0
  bucket = aws_s3_bucket.synthetics_artifacts[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "synthetics_artifacts" {
  count  = var.create_synthetics ? 1 : 0
  bucket = aws_s3_bucket.synthetics_artifacts[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

##########################################################
# Archive Files for Canary Scripts
##########################################################
data "archive_file" "canary_scripts" {
  for_each = var.create_synthetics ? var.canaries : {}

  type        = "zip"
  output_path = "${path.module}/scripts/${each.value.name}.zip"

  source {
    content = <<EOF
const synthetics = require('Synthetics');
const configuration = synthetics.getConfiguration();

const pageLoadBlueprint = async function () {
    const url = '${each.value.target_url}';
    
    const page = await synthetics.getPage();
    const response = await page.goto(url, {waitUntil: 'networkidle0', timeout: 30000});
    
    if (response.status() !== 200) {
        throw "Failed to load page";
    }
};

exports.handler = async () => {
    return await pageLoadBlueprint();
};
EOF
    filename = "index.js"
  }
}

##########################################################
# S3 Objects for Canary Scripts (ZIP files)
##########################################################
resource "aws_s3_object" "canary_scripts" {
  for_each = var.create_synthetics ? var.canaries : {}

  bucket = aws_s3_bucket.synthetics_artifacts[0].bucket
  key    = "canary-scripts/${each.value.name}.zip"
  source = data.archive_file.canary_scripts[each.key].output_path

  tags = merge(
    {
      Name        = "${each.value.name}-script"
      Project     = var.project_name
      Service     = "synthetics-script"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
}

##########################################################
# Synthetics Canaries
##########################################################
resource "aws_synthetics_canary" "canaries" {
  for_each = var.create_synthetics ? var.canaries : {}

  name                 = each.value.name
  artifact_s3_location = "s3://${aws_s3_bucket.synthetics_artifacts[0].bucket}/canary-artifacts/${each.value.name}/"
  execution_role_arn   = aws_iam_role.synthetics_role[0].arn
  runtime_version      = each.value.runtime_version
  start_canary         = each.value.start_canary
  handler              = "index.handler"

  # Source code from S3 (ZIP file)
  s3_bucket = aws_s3_bucket.synthetics_artifacts[0].bucket
  s3_key    = aws_s3_object.canary_scripts[each.key].key

  schedule {
    expression = each.value.schedule_expression
  }

  run_config {
    timeout_in_seconds = each.value.timeout_in_seconds
    memory_in_mb       = each.value.memory_in_mb
    active_tracing     = each.value.active_tracing
  }

  vpc_config {
    subnet_ids         = each.value.subnet_ids
    security_group_ids = each.value.security_group_ids
  }

  tags = merge(
    {
      Name        = each.value.name
      Project     = var.project_name
      Service     = "synthetics-canary"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
}

##########################################################
# CloudWatch Alarms for Canaries
##########################################################
resource "aws_cloudwatch_metric_alarm" "canary_alarms" {
  for_each = var.create_synthetics ? var.canaries : {}

  alarm_name          = "${each.value.name}-canary-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FailedRequests"
  namespace           = "CloudWatchSynthetics"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "This metric monitors canary failed requests"
  alarm_actions       = var.alarm_actions

  dimensions = {
    CanaryName = aws_synthetics_canary.canaries[each.key].name
  }

  tags = merge(
    {
      Name        = "${each.value.name}-canary-alarm"
      Project     = var.project_name
      Service     = "synthetics-alarm"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
} 