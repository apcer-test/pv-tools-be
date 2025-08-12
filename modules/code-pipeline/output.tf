output "pipeline_name" {
  description = "The name of the CodePipeline."
  value       = try(aws_codepipeline.codepipeline[0].name, null)
}

output "pipeline_arn" {
  description = "The ARN of the CodePipeline."
  value       = try(aws_codepipeline.codepipeline[0].arn, null)
}

output "build_project_name" {
  description = "The name of the build CodeBuild project."
  value       = try(aws_codebuild_project.build_project[0].name, null)
}

output "ecs_build_project_name" {
  description = "The name of the ECS build CodeBuild project."
  value       = try(aws_codebuild_project.ecs_build_project[0].name, null)
}

output "cloudfront_project_name" {
  description = "The name of the CloudFront invalidate CodeBuild project."
  value       = try(aws_codebuild_project.invalidate_cloudfront[0].name, null)
}