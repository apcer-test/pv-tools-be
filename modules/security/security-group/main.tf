# Security Groups module
# Creates and manages security groups with flexible ingress/egress rules

# Security Group
resource "aws_security_group" "security_group" {
  count       = var.create_security_group ? 1 : 0
  name        = var.security_group_name
  description = var.security_group_description
  vpc_id      = var.vpc_id

  tags = merge(
    {
      Name        = var.security_group_name
      Project     = var.project_name
      Service     = "security-group-${var.project_name}-${var.env}"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
}

# Ingress Rules with CIDR blocks (conditional)
resource "aws_security_group_rule" "ingress_cidr" {
  count             = var.create_security_group && var.use_cidr_rules ? length(var.ingress_rules_cidr) : 0
  type              = "ingress"
  from_port         = var.ingress_rules_cidr[count.index].from_port
  to_port           = var.ingress_rules_cidr[count.index].to_port
  protocol          = var.ingress_rules_cidr[count.index].protocol
  description       = var.ingress_rules_cidr[count.index].description
  cidr_blocks       = [var.ingress_rules_cidr[count.index].cidr_blocks]
  security_group_id = aws_security_group.security_group[0].id
}

# Ingress Rules with Security Group sources (conditional)
resource "aws_security_group_rule" "ingress_sg" {
  count                    = var.create_security_group && var.use_sg_rules ? length(var.ingress_rules_sg) : 0
  type                     = "ingress"
  from_port                = var.ingress_rules_sg[count.index].from_port
  to_port                  = var.ingress_rules_sg[count.index].to_port
  protocol                 = var.ingress_rules_sg[count.index].protocol
  description              = var.ingress_rules_sg[count.index].description
  source_security_group_id = var.ingress_rules_sg[count.index].source_security_group_id
  security_group_id        = aws_security_group.security_group[0].id
}

# Egress Rules with CIDR blocks (conditional)
resource "aws_security_group_rule" "egress_cidr" {
  count             = var.create_security_group && var.use_cidr_rules ? length(var.egress_rules_cidr) : 0
  type              = "egress"
  from_port         = var.egress_rules_cidr[count.index].from_port
  to_port           = var.egress_rules_cidr[count.index].to_port
  protocol          = var.egress_rules_cidr[count.index].protocol
  description       = var.egress_rules_cidr[count.index].description
  cidr_blocks       = [var.egress_rules_cidr[count.index].cidr_blocks]
  security_group_id = aws_security_group.security_group[0].id
}

# Egress Rules with Security Group sources (conditional)
resource "aws_security_group_rule" "egress_sg" {
  count                    = var.create_security_group && var.use_sg_rules ? length(var.egress_rules_sg) : 0
  type                     = "egress"
  from_port                = var.egress_rules_sg[count.index].from_port
  to_port                  = var.egress_rules_sg[count.index].to_port
  protocol                 = var.egress_rules_sg[count.index].protocol
  description              = var.egress_rules_sg[count.index].description
  source_security_group_id = var.egress_rules_sg[count.index].source_security_group_id
  security_group_id        = aws_security_group.security_group[0].id
} 