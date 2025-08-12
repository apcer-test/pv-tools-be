# EC2 Bastion Host (Only created when both bastion and VPC are enabled)
module "ec2-bastion" {
  count  = var.create_bastion && var.create_vpc ? 1 : 0
  source = "../modules/ec2-bastion"
  
  create_bastion              = true
  create_admin_key            = true  # Auto-enabled when bastion is created
  create_developer_key        = true  # Auto-enabled when bastion is created
  bastion_name                = "bastion-${var.project_name}-${var.env}"
  project_name                = var.project_name
  env                         = var.env
  ami_id                      = var.bastion_ami_id
  instance_type               = var.bastion_instance_type
  subnet_id                   = module.vpc.public_subnet_ids[0]  # Use first public subnet
  vpc_security_group_ids      = concat([module.ec2-bastion-sg[0].security_group_id], var.bastion_security_group_ids)
  volume_size                 = var.bastion_volume_size
  enable_instance_scheduler   = var.bastion_enable_instance_scheduler
  disable_api_termination     = var.bastion_disable_api_termination
} 