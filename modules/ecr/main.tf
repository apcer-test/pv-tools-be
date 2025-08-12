# ECR Module - Creates multiple ECR repositories

# ECR Repositories
module "ecr_repositories" {
  source  = "terraform-aws-modules/ecr/aws"
  version = "2.4.0"
  
  count = var.create_ecr_repositories ? length(var.ecr_repositories) : 0

  create_repository       = true
  repository_type        = "private"
  repository_name        = var.ecr_repositories[count.index].name
  repository_force_delete = var.ecr_repositories[count.index].force_delete

  # Image scanning configuration
  repository_image_scan_on_push = var.ecr_repositories[count.index].scan_on_push

  # Lifecycle policy for image retention
  repository_lifecycle_policy = jsonencode({
    rules = [
      {
        rulePriority = 1,
        description  = "Keep the last ${var.ecr_repositories[count.index].retention_count} images",
        selection = {
          tagStatus     = "tagged",
          tagPrefixList = ["v"],
          countType     = "imageCountMoreThan",
          countNumber   = var.ecr_repositories[count.index].retention_count
        },
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2,
        description  = "Delete untagged images older than 1 day",
        selection = {
          tagStatus   = "untagged",
          countType   = "sinceImagePushed",
          countUnit   = "days",
          countNumber = 1
        },
        action = {
          type = "expire"
        }
      }
    ]
  })

  tags = merge(
    {
      Name        = var.ecr_repositories[count.index].name
      Project     = var.project_name
      Service     = "ecr-${var.project_name}-${var.env}"
      Environment = var.env
      Repository  = var.ecr_repositories[count.index].name
      Terraform   = "true"
    },
    var.tags
  )
} 