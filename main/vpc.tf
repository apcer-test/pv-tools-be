module "vpc" {
  source                        = "../modules/vpc"
  project_name                  = var.project_name
  env                           = var.env
  create_vpc                    = var.create_vpc
  cidr                          = var.cidr
  availability_zones            = var.vpc_availability_zones
  create_database_subnet_group  = var.create_database_subnet_group
}