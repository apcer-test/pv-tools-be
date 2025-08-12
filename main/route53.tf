# Route53 Configuration
# Creates DNS records and hosted zone management

# Route53 Module
module "route53" {
  count  = var.create_route53 ? 1 : 0
  source = "../modules/route53"

  create_hosted_zone = true  # Create new hosted zone
  domain_name        = var.route53_domain_name
  zone_id            = var.route53_zone_id  # Only used if create_hosted_zone = false
  
  # DNS Records
  a_records     = var.route53_a_records
  cname_records = var.route53_cname_records
  mx_records    = var.route53_mx_records
  txt_records   = var.route53_txt_records
  alias_records = var.route53_alias_records
  health_checks = var.route53_health_checks
  failover_records = var.route53_failover_records
  
  project_name = var.project_name
  env          = var.env
} 