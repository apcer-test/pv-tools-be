# SSH Keys Module - Creates SSH key pairs for bastion access

# Admin SSH Key Pair (for full bastion access)
resource "aws_key_pair" "admin_key" {
  count           = var.create_admin_key ? 1 : 0
  key_name        = "${var.project_name}-${var.env}-admin-key"
  public_key      = tls_private_key.admin_key[0].public_key_openssh

  tags = merge(
    {
      Name        = "${var.project_name}-${var.env}-admin-key"
      Project     = var.project_name
      Service     = "ssh-keys-${var.project_name}-${var.env}"
      Environment = var.env
      Terraform   = "true"
    }
  )
}

# Generate private key for admin access
resource "tls_private_key" "admin_key" {
  count     = var.create_admin_key ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Developer SSH Key Pair (for tunnel-only access)
resource "aws_key_pair" "developer_key" {
  count           = var.create_developer_key ? 1 : 0
  key_name        = "${var.project_name}-${var.env}-developer-key"
  public_key      = tls_private_key.developer_key[0].public_key_openssh

  tags = merge(
    {
      Name        = "${var.project_name}-${var.env}-developer-key"
      Project     = var.project_name
      Service     = "ssh-keys-${var.project_name}-${var.env}"
      Environment = var.env
      Terraform   = "true"
    }
  )
}

# Generate private key for developer tunnel access
resource "tls_private_key" "developer_key" {
  count     = var.create_developer_key ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = 4096
} 