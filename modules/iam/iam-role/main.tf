# IAM Role Module 

# Data source to get current AWS account details
data "aws_caller_identity" "current" {}

# IAM Role
resource "aws_iam_role" "iam_role" {
  count                   = var.create_iam_role ? 1 : 0
  name                    = var.iam_role_name
  description             = var.iam_role_description

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = var.trusted_role_services
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(
    {
      Name        = var.iam_role_name
      Project     = var.project_name
      Service     = "iam-role-${var.project_name}-${var.env}"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
}

# Combine all policy ARNs (managed + custom)
locals {
  all_policy_arns = var.create_iam_role ? concat(
    var.custom_role_policy_arns,
    var.additional_policy_arns
  ) : []
}

# Attach all policies to the role (managed + custom)
resource "aws_iam_role_policy_attachment" "policies" {
  count         = var.create_iam_role ? length(local.all_policy_arns) : 0
  role          = aws_iam_role.iam_role[0].name
  policy_arn    = local.all_policy_arns[count.index]
  depends_on    = [aws_iam_role.iam_role]
} 