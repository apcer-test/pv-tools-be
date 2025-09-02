

locals {
  # Determine provider type based on repository type
  provider_type = var.repository_type == "github" ? "GitHub" : (
    var.repository_type == "gitlab-com" ? "GitLab" : "GitLabSelfManaged"
  )
  
  # Use host ARN only for GitLab self-hosted
  use_host_arn = var.repository_type == "gitlab-self-hosted"
  
  # All services use custom buildspec from repository
  dynamic_buildspec = null
  





}

# CodeStar Connection for GitLab self-hosted (uses host_arn)
resource "aws_codestarconnections_connection" "codestar_connection_gitlab_hosted" {
  count    = var.enabled && local.use_host_arn ? 1 : 0
  name     = var.codestart_connection_name
  host_arn = var.codestart_connection_gitlab_host_arn
}

# CodeStar Connection for GitLab.com or GitHub (uses provider_type)
resource "aws_codestarconnections_connection" "codestar_connection_public" {
  count         = var.enabled && !local.use_host_arn ? 1 : 0
  name          = var.codestart_connection_name
  provider_type = local.provider_type
}

# Local to get the correct connection ARN
locals {
  connection_arn = var.use_existing_connection ? var.existing_connection_arn : (
    local.use_host_arn ? (
      length(aws_codestarconnections_connection.codestar_connection_gitlab_hosted) > 0 ? 
      aws_codestarconnections_connection.codestar_connection_gitlab_hosted[0].arn : ""
    ) : (
      length(aws_codestarconnections_connection.codestar_connection_public) > 0 ? 
      aws_codestarconnections_connection.codestar_connection_public[0].arn : ""
    )
  )
}

resource "aws_codebuild_project" "build_project" {
  count        = var.enabled && (var.enable_build_stage || var.enable_serverless_stage) ? 1 : 0
  name         = var.build_project_name
  description  = "Build project for ${var.name}-${var.app} (${var.service_type})"
  service_role = var.iam_role_arn
  build_timeout = 60

  source {
    type = "CODEPIPELINE"
    buildspec = null  # Always use custom buildspec from repository
  }

  environment {
    compute_type = var.build_compute_type
    image        = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type         = "LINUX_CONTAINER"
    
    # All environment variables come from env_vars to avoid duplicates
    dynamic "environment_variable" {
      for_each = var.enable_env_vars ? var.env_vars : []
      content {
        name  = environment_variable.value.name
        value = environment_variable.value.value
        type  = lookup(environment_variable.value, "type", "PLAINTEXT")
      }
    }
  }

  artifacts {
    type = "CODEPIPELINE"
  }
}

resource "aws_codebuild_project" "invalidate_cloudfront" {
  count        = var.enabled && var.enable_invalidate_stage ? 1 : 0
  name         = var.cloudfront_project_name
  service_role = var.iam_role_arn

  environment {
    compute_type = "BUILD_GENERAL1_SMALL"
    image        = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type         = "LINUX_CONTAINER"
    environment_variable {
      name  = "DISTRIBUTION_ID"
      value = var.cloudfront_distribution_id
    }
  }


  
  source {
    type = "NO_SOURCE"
    buildspec = <<EOF
    version: 0.2
    phases:
      build:
        commands:
          - echo "Checking CloudFront distribution ID..."
          - |
            if [ -z "$DISTRIBUTION_ID" ]; then
              echo "ERROR: DISTRIBUTION_ID is empty. CloudFront distribution may not exist yet."
              echo "Skipping CloudFront invalidation."
              exit 0
            fi
          - aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths '/*'
    EOF

  }



  artifacts {
    type = "NO_ARTIFACTS"
  }
}

resource "aws_codebuild_project" "ecs_build_project" {
  count        = var.enabled && var.enable_ecr_build_stage ? 1 : 0
  name         = var.ecs_build_project_name
  description  = "ECS Build project for ${var.name}-${var.app}"
  service_role = var.iam_role_arn
  build_timeout = 60

  source {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type = var.ecs_build_compute_type
    image        = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type         = "LINUX_CONTAINER"
    
    dynamic "environment_variable" {
      for_each = var.env_vars
      content {
        name  = environment_variable.value.name
        value = environment_variable.value.value
        type  = lookup(environment_variable.value, "type", "PLAINTEXT")
      }
    }
  }

  artifacts {
    type = "CODEPIPELINE"
  }
}

resource "aws_codepipeline" "codepipeline" {
  count        = var.enabled ? 1 : 0
  name         = var.pipeline_name
  role_arn     = var.iam_role_arn
  pipeline_type = "V2"

  artifact_store {
    location = var.codepipeline_artifacts_bucket
    type     = "S3"
  }

  trigger {
    provider_type = "CodeStarSourceConnection"
    git_configuration {
      source_action_name = "PullCode"
      push {
        tags {
          includes = ["${var.name}-${var.env}-*"]
        }
      }
    }
  }

  dynamic "stage" {
    for_each = var.enable_source_stage ? [1] : []
    content {
      name = "Source"
      action {
        name             = "PullCode"
        category         = "Source"
        owner            = "AWS"
        provider         = "CodeStarSourceConnection"
        version          = "1"
        output_artifacts = ["source_output"]
        configuration = {
                      ConnectionArn    = local.connection_arn
          FullRepositoryId = var.full_repo_path
          BranchName       = var.repo_branch
        }
      }
    }
  }

  dynamic "stage" {
    for_each = var.enable_build_stage ? [1] : []
    content {
      name = "Build"
      action {
        name             = "CodeBuild"
        category         = "Build"
        owner            = "AWS"
        provider         = "CodeBuild"
        input_artifacts  = ["source_output"]
        output_artifacts = ["build_output"]
        version          = "1"
        configuration = {
          ProjectName = aws_codebuild_project.build_project[0].name
        }
      }
    }
  }

  dynamic "stage" {
    for_each = var.enable_ecr_build_stage ? [1] : []
    content {
      name = "Build"
      action {
        name             = "CodeBuild"
        category         = "Build"
        owner            = "AWS"
        provider         = "CodeBuild"
        input_artifacts  = ["source_output"]
        output_artifacts = ["build_output"]
        version          = "1"
        configuration = {
          ProjectName = aws_codebuild_project.ecs_build_project[0].name
        }
      }
    }
  }

  dynamic "stage" {
    for_each = var.enable_deploy_stage ? [1] : []
    content {
      name = "Deploy"
      action {
        name             = "DeployToS3"
        category         = "Deploy"
        owner            = "AWS"
        provider         = "S3"
        input_artifacts  = ["build_output"]
        version          = "1"
        configuration = {
          BucketName = var.s3_bucket_name
          Extract    = "true"
        }
      }
    }
  }

  dynamic "stage" {
    for_each = var.enable_invalidate_stage ? [1] : []
    content {
      name = "Invalidate"
      action {
        name            = "InvalidateCloudFront"
        category        = "Build"
        owner           = "AWS"
        provider        = "CodeBuild"
        input_artifacts = ["build_output"]
        version         = "1"
        configuration = {
          ProjectName = aws_codebuild_project.invalidate_cloudfront[0].name
        }
      }
    }
  }

  dynamic "stage" {
    for_each = var.enable_ecs_deploy_stage ? [1] : []
    content {
      name = "ECSDeploy"
      action {
        name             = "DeployToECS"
        category         = "Deploy"
        owner            = "AWS"
        provider         = "ECS"
        input_artifacts  = ["build_output"]
        version          = "1"
        configuration = {
          ClusterName = var.ecs_cluster_name
          ServiceName = var.ecs_service_name
          FileName    = "imagedefinitions.json"
        }
      }
    }
  }

  dynamic "stage" {
    for_each = var.enable_serverless_stage ? [1] : []
    content {
      name = "ServerlessDeploy"
      action {
        name             = "ServerlessDeployment"
        category         = "Build"
        owner            = "AWS"
        provider         = "CodeBuild"
        input_artifacts  = ["source_output"]
        version          = "1"
        configuration = {
          ProjectName = aws_codebuild_project.build_project[0].name
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      stage[0].action[0].configuration["OutputArtifactFormat"],
      stage[1].action[0].configuration["OutputArtifactFormat"],
      stage[2].action[0].configuration["OutputArtifactFormat"],
      stage[3].action[0].configuration["OutputArtifactFormat"],
      stage[4].action[0].configuration["OutputArtifactFormat"]
    ]
  }
}

resource "aws_codepipeline_webhook" "pipeline_webhook" {
  count = var.enabled && var.create_codepipeline_webhook ? 1 : 0
  name                          = "${var.pipeline_name}-webhook"
  authentication                = var.pipeline_webhook_authentication
  target_action                 = "PullCode"
  target_pipeline               = aws_codepipeline.codepipeline[0].name

  lifecycle {
    ignore_changes = [authentication_configuration[0].secret_token]
  }

  authentication_configuration {
    secret_token      = var.pipeline_webhook_authentication == "GITHUB_HMAC" ? var.aws_secret_string : null
    allowed_ip_range  = var.pipeline_webhook_authentication == "IP" ? var.webhook_allowed_ip : null
  }

  filter {
    json_path    = "$.ref"
    match_equals = var.pipeline_webhook_filter_match
  }
} 