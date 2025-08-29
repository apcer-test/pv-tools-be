########       IAM ROLE        ########
module "iam_custom_policy_codepipeline" {
  source                        = "../modules/iam/iam-policy"
  project_name                  = var.project_name
  env                           = var.env
  create_iam_policy             = var.create_codepipelines
  iam_policy_name               = "${var.project_name}-${var.env}-codepipeline-custom-policy"
  region                        = var.region
  description                   = "Custom policy for CodePipeline services"
  # Comprehensive CodePipeline permissions via custom policy module
  attach_cloudwatch_policy      = true    # CloudWatch logs and metrics
  attach_rds_policy             = false   # Not needed for pipelines
  attach_s3_bucket_policy       = true    # S3 for artifacts storage
  attach_cloudfront_access      = true    # CloudFront invalidation
  attach_lambda_access          = true    # Lambda deployment
  attach_iam_role               = true    # IAM role management
  attach_ecr_policy             = true    # ECR for container images
  attach_ecs_policy             = true    # ECS deployments
  attach_codebuild_policy       = true    # CodeBuild projects
  attach_codepipeline_policy    = true    # CodePipeline management
  attach_secrets_manager_policy = true    # Secrets Manager access
  attach_api_gateway_policy     = true    # API Gateway deployments
  attach_cloudformation_policy  = true    # CloudFormation stack management
  attach_sqs_policy             = true    # SQS for pipeline notifications
  account_id                    = local.account_id  # Use automatically fetched account ID
}

module "iam_assumable_role" {
  source                 = "../modules/iam/iam-role"
  project_name           = var.project_name
  env                    = var.env
  create_iam_role        = var.create_codepipelines
  iam_role_name          = var.env == "uat" ? "${var.project_name}-pipeline-role" : "${var.project_name}-${var.env}-pipeline-role"
  
  # All permissions now handled by custom policy module - no AWS managed policies needed!
  custom_role_policy_arns = var.create_codepipelines ? [module.iam_custom_policy_codepipeline.policy_arn] : []
  
  trusted_role_services = [
    "codebuild.amazonaws.com",
    "codepipeline.amazonaws.com", 
    "codedeploy.amazonaws.com"
  ]
  
  tags = merge(local.common_tags, {
    Service = "pipeline-role"
  })
}

########       DYNAMIC CODE PIPELINES        ########

locals {
  # Check if required S3 buckets exist for CodePipeline
  codepipeline_buckets_exist = contains(keys(var.storage_buckets), "codepipeline_artifacts_bucket") && contains(keys(var.storage_buckets), "env_bucket")
  
  # Create pipelines for frontend services from frontends configuration
  frontend_pipelines = var.create_codepipelines && local.codepipeline_buckets_exist ? {
    for frontend_key, frontend in var.frontends : "${frontend_key}-pipeline" => {
        # Use explicit service name from configuration
        service_name    = frontend.service_name
        service_type    = "frontend"
        pipeline_name   = "${frontend.service_name}-${var.env}"
        repo_path       = frontend.repository_path
        repo_branch     = frontend.repository_branch
        connection_name = "${frontend.service_name}-${var.env}"
      
      # Frontend-specific configuration
      enable_build_stage        = true
      enable_deploy_stage       = true
      enable_invalidate_stage   = true
      enable_ecr_build_stage    = false
      enable_ecs_deploy_stage   = false
      enable_serverless_stage   = false
      
      # Build configuration
      build_project_name        = "${var.project_name}-${frontend.service_name}-${var.env}"
      cloudfront_project_name   = "${var.project_name}-${frontend.service_name}-${var.env}-invalidate-cloudfront"
      s3_bucket_name           = "${var.project_name}-${frontend.service_name}-${var.env}-bucket"
      env_file_s3_path         = frontend.bucket_path
      
      # Build settings from frontend configuration
      node_version      = frontend.node_version
      build_commands    = frontend.build_commands
      install_commands  = try(frontend.install_commands, [])
      compute_type      = try(frontend.compute_type, "BUILD_GENERAL1_SMALL")
      
      # CloudFront distribution ID (to be populated from CloudFront module)
      cloudfront_distribution_id = try(module.cloudfront_s3["${frontend_key}-cloudfront"].cloudfront_distribution_id, "")
      
      env_vars = [
        {
          name  = "S3_BUCKET"
          value = contains(keys(module.s3), "env_bucket") ? module.s3["env_bucket"].bucket_name : ""
        },
        {
          name  = "BUCKET_PATH"
          value = frontend.bucket_path
        }
      ]
    } if try(frontend.create_codepipeline, false) && try(frontend.create, true)
  } : {}
  
  # Create pipelines for ECS services (only for services with repository_path defined and required buckets exist)
  ecs_pipelines = var.create_ecs_ecosystem && var.create_codepipelines && local.codepipeline_buckets_exist ? {
    for service_key, service in var.services : service.container_name => {
      # Use container name for pipeline and connection naming for ECS services
      service_name    = service.container_name
      service_type    = "ecs"
      pipeline_name   = "${service.container_name}-${var.env}"
      repo_path       = service.repository_path
      repo_branch     = service.repository_branch
      # Create separate connections for each service
      connection_name = "${service.container_name}-${var.env}"
      
      # ECS-specific configuration
      enable_build_stage        = false
      enable_deploy_stage       = false
      enable_invalidate_stage   = false
      enable_ecr_build_stage    = true
      enable_ecs_deploy_stage   = true
      enable_serverless_stage   = false
      
      # Build configuration
      build_project_name        = ""
      ecs_build_project_name    = "${var.project_name}-${service.container_name}-ecs-${var.env}"
      cloudfront_project_name   = ""
      s3_bucket_name           = ""
      env_file_s3_path         = service.env_bucket_path
      
      # ECS configuration
      container_name    = service.container_name
      ecs_cluster_name  = "${var.project_name}-cluster-${var.env}"
      ecs_service_name  = "${var.project_name}-${service.container_name}-${var.env}"
      compute_type      = service.compute_type
      
      # Build settings
      node_version      = ""
      build_commands    = []
      install_commands  = []
      
      cloudfront_distribution_id = ""
      env_vars = [
        {
          name  = "ECS_REPOSITORY_URI"
          value = "${local.account_id}.dkr.ecr.${var.region}.amazonaws.com/${var.project_name}-${service.container_name}-${var.env}"
        },
        {
          name  = "ECR_LOGIN"
          value = "${local.account_id}.dkr.ecr.${var.region}.amazonaws.com"
        },
        {
          name  = "CONTAINER_NAME"
          value = service.container_name
        },
        {
          name  = "S3_BUCKET"
          value = contains(keys(module.s3), "env_bucket") ? module.s3["env_bucket"].bucket_name : ""
        },
        {
          name  = "BUCKET_PATH"
          value = service.env_bucket_path
        },
        {
          name  = "REGION"
          value = var.region
        }
      ]
    } if service.repository_path != ""  # Only create pipeline if repository_path is provided
  } : {}
  
  # Create pipelines for serverless services
  serverless_pipelines = var.create_codepipelines && local.codepipeline_buckets_exist ? {
    for service_key, service_config in var.serverless_microservices_codepipeline : service_key => {
      # Use explicit service name from configuration
      service_name    = service_config.service_name
      service_type    = "serverless"
      pipeline_name   = "${service_config.service_name}-${var.env}"
      repo_path       = service_config.repository_path
      repo_branch     = service_config.repository_branch
      connection_name = "${service_config.service_name}-${var.env}"
      
      # Serverless-specific configuration
      enable_build_stage        = false
      enable_deploy_stage       = false
      enable_invalidate_stage   = false
      enable_ecr_build_stage    = false
      enable_ecs_deploy_stage   = false
      enable_serverless_stage   = true
      
      # Build configuration
      build_project_name        = "${var.project_name}-${service_key}-${var.env}"
      cloudfront_project_name   = ""
      s3_bucket_name           = ""
      env_file_s3_path         = service_config.bucket_path
      
      # Build settings from service configuration
      node_version      = service_config.node_version
      build_commands    = service_config.build_commands
      install_commands  = service_config.install_commands
      compute_type      = try(service_config.compute_type, "BUILD_GENERAL1_SMALL")
      serverless_stage  = var.env
      
      cloudfront_distribution_id = ""
      env_vars = [
        {
          name  = "STAGE"
          value = var.env
        },
        {
          name  = "REGION"
          value = var.region
        },
        {
          name  = "S3_BUCKET"
          value = contains(keys(module.s3), "env_bucket") ? module.s3["env_bucket"].bucket_name : ""
        },
        {
          name  = "BUCKET_PATH"
          value = service_config.bucket_path
        }
      ]
    }
  } : {}
  
  # Merge all pipeline configurations
  all_pipelines = merge(
    local.frontend_pipelines,
    local.ecs_pipelines,
    local.serverless_pipelines
  )
}



# Create CodePipelines from dynamic configuration
module "codepipeline" {
  for_each = local.all_pipelines
  source   = "../modules/code-pipeline"
  
  enabled                       = true
  enable_env_vars               = true
  name                          = var.project_name
  app                           = "pipeline-${each.key}"
  env                           = var.env
  
  # Pipeline configuration
  pipeline_name                 = each.value.pipeline_name
  service_type                  = each.value.service_type
  repository_type               = var.version_control_type
  
  # Stage configuration based on service type
  enable_source_stage           = true
  enable_build_stage            = each.value.enable_build_stage
  enable_deploy_stage           = each.value.enable_deploy_stage
  enable_invalidate_stage       = each.value.enable_invalidate_stage
  enable_ecr_build_stage        = each.value.enable_ecr_build_stage
  enable_ecs_deploy_stage       = each.value.enable_ecs_deploy_stage
  enable_serverless_stage       = each.value.enable_serverless_stage
  
  # Common configuration - conditional S3 bucket reference
  codepipeline_artifacts_bucket = contains(keys(module.s3), "codepipeline_artifacts_bucket") ? module.s3["codepipeline_artifacts_bucket"].bucket_name : ""
  iam_role_arn                  = module.iam_assumable_role.iam_role_arn
  region                        = var.region
  
  # S3 and environment configuration
  s3_bucket_name                = each.value.s3_bucket_name
  env_file_s3_path              = each.value.env_file_s3_path
  
  # Build project names
  build_project_name            = each.value.build_project_name
  ecs_build_project_name        = lookup(each.value, "ecs_build_project_name", "")
  cloudfront_project_name       = each.value.cloudfront_project_name
  cloudfront_distribution_id    = each.value.cloudfront_distribution_id
  
  # ECS-specific configuration (for deployment stage, not build env vars)
  container_name                = lookup(each.value, "container_name", "")
  ecs_cluster_name              = lookup(each.value, "ecs_cluster_name", "")
  ecs_service_name              = lookup(each.value, "ecs_service_name", "")
  
  # Repository configuration
  full_repo_path                = each.value.repo_path
  repo_branch                   = each.value.repo_branch
  codestart_connection_name     = each.value.connection_name

  
  # Build configuration
  build_compute_type            = lookup(each.value, "compute_type", "BUILD_GENERAL1_SMALL")
  ecs_build_compute_type        = lookup(each.value, "compute_type", "BUILD_GENERAL1_SMALL")
  node_version                  = each.value.node_version
  build_commands                = each.value.build_commands
  install_commands              = each.value.install_commands
  serverless_stage              = lookup(each.value, "serverless_stage", var.env)
  create_codepipeline_webhook   = false
  use_custom_buildspec          = lookup(each.value, "use_custom_buildspec", false)
  
  # Environment variables
  env_vars                      = each.value.env_vars
  
  depends_on = [
    module.s3,                  # Ensure S3 buckets are created first
    module.iam_assumable_role,
    module.cloudfront_s3        # Ensure CloudFront distributions are created first
  ]
}


