# SSH Keys Module Outputs

# Admin Key Outputs
output "admin_key_name" {
  description = "Name of the admin SSH key pair"
  value       = var.create_admin_key ? aws_key_pair.admin_key[0].key_name : null
}

output "admin_public_key" {
  description = "Public key content for admin access"
  value       = var.create_admin_key ? tls_private_key.admin_key[0].public_key_openssh : null
}

output "admin_private_key" {
  description = "Private key content for admin access (sensitive)"
  value       = var.create_admin_key ? tls_private_key.admin_key[0].private_key_pem : null
  sensitive   = true
}

# Developer Key Outputs
output "developer_key_name" {
  description = "Name of the developer SSH key pair"
  value       = var.create_developer_key ? aws_key_pair.developer_key[0].key_name : null
}

output "developer_public_key" {
  description = "Public key content for developer tunnel access"
  value       = var.create_developer_key ? tls_private_key.developer_key[0].public_key_openssh : null
}

output "developer_private_key" {
  description = "Private key content for developer tunnel access (sensitive)"
  value       = var.create_developer_key ? tls_private_key.developer_key[0].private_key_pem : null
  sensitive   = true
}

# Key Information Summary
output "ssh_keys_info" {
  description = "Summary of created SSH keys"
  value = {
    admin_key_created     = var.create_admin_key
    developer_key_created = var.create_developer_key
    admin_key_name        = var.create_admin_key ? aws_key_pair.admin_key[0].key_name : null
    developer_key_name    = var.create_developer_key ? aws_key_pair.developer_key[0].key_name : null
    admin_key_id          = var.create_admin_key ? aws_key_pair.admin_key[0].key_pair_id : null
    developer_key_id      = var.create_developer_key ? aws_key_pair.developer_key[0].key_pair_id : null
  }
} 