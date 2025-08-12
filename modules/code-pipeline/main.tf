

locals {
  # Determine provider type based on repository type
  provider_type = var.repository_type == "github" ? "GitHub" : (
    var.repository_type == "gitlab-com" ? "GitLab" : "GitLabSelfManaged"
  )
  
  # Use host ARN only for GitLab self-hosted
  use_host_arn = var.repository_type == "gitlab-self-hosted"
  
  # Dynamic buildspec based on service type
  dynamic_buildspec = var.service_type == "frontend" ? local.frontend_buildspec : (
    var.service_type == "serverless" ? local.serverless_buildspec : local.ecs_buildspec
  )
  
  # Frontend buildspec
  frontend_buildspec = <<EOF
version: 0.2
phases:
  install:
    runtime-versions:
      nodejs: ${var.node_version}
    commands:
      - echo Installing dependencies....
      - aws --version
      - aws s3 cp s3://$$S3_BUCKET/$$BUCKET_PATH/.env .env
      - ls -la
      - cat .env
%{ for command in slice(var.build_commands, 0, min(2, length(var.build_commands))) }
      - ${command}
%{ endfor }
  build:
    commands:
%{ if length(var.build_commands) > 2 }
%{ for command in slice(var.build_commands, 2, length(var.build_commands)) }
      - ${command}
%{ endfor }
%{ endif }
      - ls -la dist
artifacts:
  files:
    - "**/*"
  base-directory: dist
  discard-paths: no
EOF

  # Serverless buildspec
  serverless_buildspec = <<EOF
version: 0.2
phases:
  install:
    runtime-versions:
      nodejs: ${var.node_version != "" ? var.node_version : "20.9.0"}
    commands:
      - echo "Installing required dependencies"
%{ if length(var.install_commands) > 0 }
%{ for command in var.install_commands }
      - ${command}
%{ endfor }
%{ else }
      - npm install -g serverless
%{ endif }
  pre_build:
    commands:
      - echo "Setting up environment variables"
      - aws s3 cp s3://$$S3_BUCKET/$$BUCKET_PATH/.env .
      - ls -al
      - cat .env
  build:
    commands:
      - echo "Installing project dependencies"
%{ if length(var.build_commands) > 0 }
%{ for command in var.build_commands }
      - ${command}
%{ endfor }
%{ else }
      - yarn install
%{ endif }
      - echo "Deploying Serverless Application"
      - sls deploy --stage $$STAGE --region $$REGION
artifacts:
  files:
    - '**/*'
EOF

  # ECS buildspec (uses environment variables set via env_vars)
  ecs_buildspec = <<EOF
version: 0.2
phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $$REGION | docker login -u AWS --password-stdin $$ECR_LOGIN
      - echo Fetching environment variables from S3...
      - aws s3 cp s3://$$S3_BUCKET/$$BUCKET_PATH/.env .env
      - aws s3 cp s3://$$S3_BUCKET/$$BUCKET_PATH/private_key.pem private_key.pem
      - aws s3 cp s3://$$S3_BUCKET/$$BUCKET_PATH/public_key.pem public_key.pem
      - aws s3 cp s3://$$S3_BUCKET/$$BUCKET_PATH/cloudfront_private_key.pem private_key_cloudfront.pem
      - ls -la
  build:
    commands:
      - echo Building the Docker image...
      - TAG="v$${CODEBUILD_RESOLVED_SOURCE_VERSION:0:5}-$(date +%I-%M-%y-%m-%d)"
      - docker build -t $$REPOSITORY_URI:$$TAG .
  post_build:
    commands:
      - echo Pushing the Docker image...
      - docker push $$REPOSITORY_URI:$$TAG
      - echo Generating imagedefinitions.json...
      - printf '[{"name":"%s","imageUri":"%s"}]' "$$CONTAINER_NAME" "$$REPOSITORY_URI:$$TAG" > imagedefinitions.json
artifacts:
  files:
    - imagedefinitions.json
  base-directory: .
EOF
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
  connection_arn = local.use_host_arn ? (
    length(aws_codestarconnections_connection.codestar_connection_gitlab_hosted) > 0 ? 
    aws_codestarconnections_connection.codestar_connection_gitlab_hosted[0].arn : ""
  ) : (
    length(aws_codestarconnections_connection.codestar_connection_public) > 0 ? 
    aws_codestarconnections_connection.codestar_connection_public[0].arn : ""
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
    buildspec = var.force_terraform_buildspec ? local.dynamic_buildspec : (var.use_custom_buildspec ? null : local.dynamic_buildspec)
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
      - echo "Invalidating CloudFront distribution..."
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