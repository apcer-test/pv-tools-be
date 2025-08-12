# EC2 Bastion Host Module

# SSH Keys for Bastion Access
module "ssh_keys" {
  source                = "../security/ssh_keys"
  create_admin_key      = var.create_bastion && var.create_admin_key
  create_developer_key  = var.create_bastion && var.create_developer_key
  project_name          = var.project_name
  env                   = var.env
  admin_key_name        = "${var.project_name}-${var.env}-admin-key"
  developer_key_name    = "${var.project_name}-${var.env}-developer-key"
}

# Lookup the latest official Ubuntu 22.04 LTS AMI from Canonical in the current AWS region.
# Ubuntu 22.04 LTS is stable and widely available across all AWS regions.
# This ensures the bastion host always uses the most up-to-date and secure Ubuntu image,
# unless a custom AMI ID is provided.
data "aws_ami" "ubuntu" {
  count       = var.ami_id == "" ? 1 : 0
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# Prepare user data with developer public key
locals {
  user_data = templatefile("${path.module}/../../scripts/bastion-host-setup.sh", {
    developer_public_key = module.ssh_keys.developer_public_key != null ? module.ssh_keys.developer_public_key : ""
  })
}

# EC2 Instance for Bastion Host
resource "aws_instance" "bastion" {
  count                       = var.create_bastion ? 1 : 0
  ami                         = var.ami_id != "" ? var.ami_id : data.aws_ami.ubuntu[0].id
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = var.vpc_security_group_ids
  key_name                    = module.ssh_keys.admin_key_name
  associate_public_ip_address = true
  ebs_optimized               = true
  user_data_base64            = base64encode(local.user_data)
  disable_api_termination     = var.disable_api_termination

  root_block_device {
    volume_size = var.volume_size
    volume_type = "gp3"
    encrypted   = true
    delete_on_termination = true
  }

  tags = merge(
    {
      Name        = var.bastion_name
      Project     = var.project_name
      Service     = "bastion-${var.project_name}-${var.env}"
      Environment = var.env
      Terraform   = "true"
      Type        = "bastion"
    }
  )
}

# Elastic IP for Bastion Host
resource "aws_eip" "bastion_eip" {
  count         = var.create_bastion ? 1 : 0
  instance      = aws_instance.bastion[0].id
  domain        = "vpc"
  depends_on    = [aws_instance.bastion]

  tags = merge(
    {
      Name        = "${var.bastion_name}-eip"
      Project     = var.project_name
      Service     = "bastion-${var.project_name}-${var.env}"
      Environment = var.env
      Terraform   = "true"
    }
  )
} 