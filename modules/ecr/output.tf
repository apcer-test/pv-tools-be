# ECR Module Outputs

output "repository_arns" {
  description = "List of ARNs of the ECR repositories"
  value       = var.create_ecr_repositories ? module.ecr_repositories[*].repository_arn : []
}

output "repository_urls" {
  description = "List of URLs of the ECR repositories"
  value       = var.create_ecr_repositories ? module.ecr_repositories[*].repository_url : []
}

output "repository_urls_map" {
  description = "Map of repository URLs keyed by repository name"
  value = var.create_ecr_repositories ? {
    for idx, repo in var.ecr_repositories : repo.name => module.ecr_repositories[idx].repository_url
  } : {}
}

output "repository_urls_by_service" {
  description = "Map of repository URLs keyed by service key for ECS compatibility"
  value = var.create_ecr_repositories ? {
    for idx, repo in var.ecr_repositories : repo.name => module.ecr_repositories[idx].repository_url
  } : {}
}

output "repository_names" {
  description = "List of names of the ECR repositories"
  value       = var.create_ecr_repositories ? module.ecr_repositories[*].repository_name : []
}

output "repository_registry_ids" {
  description = "List of registry IDs of the ECR repositories"
  value       = var.create_ecr_repositories ? module.ecr_repositories[*].repository_registry_id : []
}

output "repositories_info" {
  description = "Complete information about all ECR repositories"
  value = var.create_ecr_repositories ? {
    for idx, repo in var.ecr_repositories : repo.name => {
      arn         = module.ecr_repositories[idx].repository_arn
      url         = module.ecr_repositories[idx].repository_url
      name        = module.ecr_repositories[idx].repository_name
      registry_id = module.ecr_repositories[idx].repository_registry_id
    }
  } : {}
} 