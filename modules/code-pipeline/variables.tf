variable "enabled" {
  description = "Whether to create this pipeline."
  type        = bool
  
}

variable "pipeline_name" {
  description = "Name of the CodePipeline."
  type        = string
}

variable "iam_role_arn" {
  description = "IAM role ARN for CodePipeline and CodeBuild."
  type        = string
}

variable "codepipeline_artifacts_bucket" {
  description = "S3 bucket for CodePipeline artifacts."
  type        = string
}

variable "codestart_connection_name" {
  description = "Name for the CodeStar connection."
  type        = string
}

variable "codestart_connection_gitlab_host_arn" {
  description = "Host ARN for CodeStar connection (GitHub/GitLab)."
  type        = string
  default     = ""
}

variable "repository_type" {
  description = "Type of repository (gitlab-self-hosted, gitlab-com, github)"
  type        = string
  default     = "gitlab-self-hosted"
  validation {
    condition = contains(["gitlab-self-hosted", "gitlab-com", "github"], var.repository_type)
    error_message = "Repository type must be one of: gitlab-self-hosted, gitlab-com, github."
  }
}

variable "service_type" {
  description = "Type of service (frontend, ecs, serverless)"
  type        = string
  validation {
    condition = contains(["frontend", "ecs", "serverless"], var.service_type)
    error_message = "Service type must be one of: frontend, ecs, serverless."
  }
}

variable "full_repo_path" {
  description = "Full repository path (e.g., org/repo)."
  type        = string
}

variable "repo_branch" {
  description = "Repository branch to use."
  type        = string
}

variable "env" {
  description = "Deployment environment (e.g., dev, prod, uat)."
  type        = string
}

variable "name" {
  description = "Short name for the service or pipeline."
  type        = string
}

variable "app" {
  description = "App name for tagging."
  type        = string
}

variable "enable_source_stage" {
  description = "Enable the source stage."
  type        = bool
  default     = true
}

variable "enable_build_stage" {
  description = "Enable the build stage."
  type        = bool
  
}

variable "enable_ecr_build_stage" {
  description = "Enable the ECR/ecs build stage."
  type        = bool
  
}

variable "enable_deploy_stage" {
  description = "Enable the deploy stage (e.g., S3)."
  type        = bool
  
}

variable "enable_invalidate_stage" {
  description = "Enable the CloudFront invalidate stage."
  type        = bool
  
}

variable "enable_ecs_deploy_stage" {
  description = "Enable the ECS deploy stage."
  type        = bool
  
}

variable "build_project_name" {
  description = "Name for the general build CodeBuild project."
  type        = string
  default     = ""
}

variable "ecs_build_project_name" {
  description = "Name for the ECS-specific build CodeBuild project."
  type        = string
  default     = ""
}

variable "cloudfront_project_name" {
  description = "Name for the CloudFront invalidate CodeBuild project."
  type        = string
  default     = ""
}

variable "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for invalidation."
  type        = string
  default     = ""
}

variable "container_name" {
  description = "Container name for ECS deployment stage."
  type        = string
  default     = ""
}

variable "region" {
  description = "AWS region."
  type        = string
  default     = "ap-south-1"
}

variable "ecs_cluster_name" {
  description = "ECS cluster name for ECS deploy stage (single cluster for all services)."
  type        = string
  default     = ""
}

variable "ecs_service_name" {
  description = "ECS service name for ECS deploy stage (unique service per pipeline)."
  type        = string
  default     = ""
}

variable "s3_bucket_name" {
  description = "S3 bucket name for S3 deploy stage."
  type        = string
  default     = ""
}

variable "build_compute_type" {
  description = "Compute type for CodeBuild."
  type        = string
  default     = "BUILD_GENERAL1_SMALL"
}

variable "ecs_build_compute_type" {
  description = "Compute type for ECS CodeBuild."
  type        = string
  default     = "BUILD_GENERAL1_SMALL"
}

variable "enable_env_vars" {
  description = "Enable environment variables for CodeBuild."
  type        = bool
  
}

variable "env_vars" {
  description = "List of environment variables for CodeBuild."
  type        = list(object({
    name  = string
    value = string
    type  = optional(string)
  }))
  default = []
}

variable "create_codepipeline_webhook" {
  description = "Whether to create a webhook for the pipeline."
  type        = bool
  
}

variable "pipeline_webhook_authentication" {
  description = "Webhook authentication type (e.g., GITHUB_HMAC, IP)."
  type        = string
  default     = "GITHUB_HMAC"
}

variable "aws_secret_string" {
  description = "Secret string for webhook authentication."
  type        = string
  default     = ""
}

variable "webhook_allowed_ip" {
  description = "Allowed IP for webhook authentication."
  type        = string
  default     = ""
}

variable "pipeline_webhook_filter_match" {
  description = "Webhook filter match string."
  type        = string
  default     = "refs/heads/{BranchName}"
}

variable "env_file_s3_path" {
  description = "S3 path for environment files."
  type        = string
  default     = ""
}

########################################
#      BUILDSPEC CONFIGURATION         #
########################################
variable "node_version" {
  description = "Node.js version for builds"
  type        = string
  default     = "20.9.0"
}

variable "build_commands" {
  description = "Build commands for the service"
  type        = list(string)
  default     = []
}

variable "install_commands" {
  description = "Install commands for serverless services"
  type        = list(string)
  default     = []
}

variable "use_custom_buildspec" {
  description = "Whether to use a custom buildspec from the repository"
  type        = bool
  default     = false
}

variable "force_terraform_buildspec" {
  description = "Whether to force use of Terraform-generated buildspec even if custom buildspec exists in repo"
  type        = bool
  default     = false
}

########################################
#      SERVERLESS CONFIGURATION        #
########################################
variable "enable_serverless_stage" {
  description = "Enable serverless deployment stage"
  type        = bool
  default     = false
}

variable "serverless_stage" {
  description = "Serverless framework stage"
  type        = string
  default     = "dev"
}

 