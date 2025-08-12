# VPC module - creates VPC with subnets, IGW, NAT

# Smart Auto-calculate subnet CIDRs - Works with ANY CIDR range
locals {
  az_count     = length(var.availability_zones)
  vpc_prefix   = tonumber(split("/", var.cidr)[1])  # Extract prefix length (e.g., 16 from "10.10.0.0/16")
  
  # Smart subnet sizing based on VPC CIDR prefix
  # Ensures optimal subnet sizes regardless of input CIDR
  subnet_newbits = (
    local.vpc_prefix <= 16 ? 8 :   # /16 or larger → /24 subnets (256 IPs)
    local.vpc_prefix <= 20 ? 4 :   # /17-/20     → /24 subnets (256 IPs) 
    local.vpc_prefix <= 24 ? 2 :   # /21-/24     → /26 subnets (64 IPs)
    1                              # /25+        → /26 subnets (64 IPs)
  )
  
  # Calculate total subnets needed (3 tiers × AZ count × safety buffer)
  total_subnets_needed = local.az_count * 3 * 2
  max_possible_subnets = pow(2, local.subnet_newbits)
  
  # Auto-generate subnet CIDRs with smart spacing
  # Pattern: Public(1-9), Private(10-19), Database(20-29) - scales with AZ count
  public_subnet_cidrs = [
    for i in range(local.az_count) : 
    cidrsubnet(var.cidr, local.subnet_newbits, i + 1)
  ]
  
  private_subnet_cidrs = [
    for i in range(local.az_count) : 
    cidrsubnet(var.cidr, local.subnet_newbits, i + 10)
  ]
  
  database_subnet_cidrs = [
    for i in range(local.az_count) : 
    cidrsubnet(var.cidr, local.subnet_newbits, i + 20)
  ]
}

# VPC creation based on condition
resource "aws_vpc" "vpc" {
  count                         = var.create_vpc ? 1 : 0
  cidr_block                    = var.cidr
  enable_dns_support            = true
  enable_dns_hostnames          = true
  instance_tenancy              = "default"

  tags = {
    Name        = "${var.project_name}-${var.env}"
    Project     = var.project_name
    Service     = "${var.project_name}-${var.env}-vpc"
    Environment = var.env
    Terraform   = "true"
  }
}


# Public subnets creation using for_each
resource "aws_subnet" "public_subnet" {
  for_each          = var.create_vpc ? toset(local.public_subnet_cidrs) : toset([])

  vpc_id                    = aws_vpc.vpc[0].id
  cidr_block                = each.value

  # Map each subnet CIDR to its corresponding AZ (1st CIDR → 1st AZ, 2nd CIDR → 2nd AZ, etc.)
  availability_zone         = var.availability_zones[index(local.public_subnet_cidrs, each.value)]
  
  map_public_ip_on_launch   = true      // instance in the public subnet will have a public IP address

  tags = {
    Name        = "${var.project_name}-${var.env}-public-subnet-${index(local.public_subnet_cidrs, each.value) + 1}"
    Project     = var.project_name
    # Create sequential subnet names: subnet-1, subnet-2, subnet-3 (CIDR position + 1)
    Service     = "${var.project_name}-${var.env}-public-subnet-${index(local.public_subnet_cidrs, each.value) + 1}"
    Environment = var.env
    Terraform   = "true"
  }
}


# Private subnets creation using for_each
resource "aws_subnet" "private_subnet" {
  for_each = var.create_vpc ? toset(local.private_subnet_cidrs) : toset([])  # Loop over private subnet CIDR blocks

  vpc_id                    = aws_vpc.vpc[0].id
  cidr_block                = each.value
  availability_zone         = var.availability_zones[index(local.private_subnet_cidrs, each.value)]

  tags = {
    Name        = "${var.project_name}-${var.env}-private-subnet-${index(local.private_subnet_cidrs, each.value) + 1}"
    Project     = var.project_name
    Service     = "${var.project_name}-${var.env}-private-subnet-${index(local.private_subnet_cidrs, each.value) + 1}"
    Environment = var.env
    Terraform   = "true"
  }
}


# Database subnets creation using for_each
resource "aws_subnet" "database_subnet" {
  for_each = var.create_vpc ? toset(local.database_subnet_cidrs) : toset([])  # Loop over database subnet CIDR blocks

  vpc_id                    = aws_vpc.vpc[0].id
  cidr_block                = each.value
  availability_zone         = var.availability_zones[index(local.database_subnet_cidrs, each.value)]

  tags = {
    Name        = "${var.project_name}-${var.env}-database-subnet-${index(local.database_subnet_cidrs, each.value) + 1}"
    Project     = var.project_name
    Service     = "${var.project_name}-${var.env}-database-subnet-${index(local.database_subnet_cidrs, each.value) + 1}"
    Environment = var.env
    Terraform   = "true"
  }
}


# DB Subnet Group for RDS
# This resource creates a DB subnet group for RDS.
# It dynamically gets all DB subnet IDs from the `aws_subnet.database_subnet` resource.
resource "aws_db_subnet_group" "default" {
  count       = var.create_vpc && var.create_database_subnet_group ? 1 : 0
  name        = "${var.project_name}-${var.env}-db-subnet-group"
  subnet_ids  = [
    for subnet in aws_subnet.database_subnet : subnet.id  # Dynamically get all DB subnet IDs
  ]

  tags = {
    Name        = "${var.project_name}-${var.env}-db-subnet-group"
    Project     = var.project_name
    Service = "${var.project_name}-${var.env}-db-subnet-group"
    Environment = var.env
    Terraform   = "true"
  }
}


# Internet Gateway - Only created if public subnets exist
resource "aws_internet_gateway" "igw" {
  count  = var.create_vpc && length(local.public_subnet_cidrs) > 0 ? 1 : 0
  vpc_id = aws_vpc.vpc[0].id

  tags = {
    Name        = "${var.project_name}-${var.env}-igw"
    Project     = var.project_name
    Service     = "${var.project_name}-${var.env}-igw"
    Environment = var.env
    Terraform   = "true"
  }
}


# Elastic IP for single NAT Gateway - Only created if private subnets exist
resource "aws_eip" "nat" {
  count  = var.create_vpc && length(local.private_subnet_cidrs) > 0 ? 1 : 0
  domain = "vpc"

  tags = {
    Name        = "${var.project_name}-${var.env}-nat-eip"
    Project     = var.project_name
    Service     = "${var.project_name}-${var.env}-nat-eip"
    Environment = var.env
    Terraform   = "true"
  }

  depends_on = [aws_internet_gateway.igw]
}

# Single NAT Gateway - Shared by all private subnets (for cost optimization)
resource "aws_nat_gateway" "nat" {
  count         = var.create_vpc && length(local.private_subnet_cidrs) > 0 ? 1 : 0
  allocation_id = aws_eip.nat[0].id
  subnet_id     = values(aws_subnet.public_subnet)[0].id  # Use first public subnet

  tags = {
    Name        = "${var.project_name}-${var.env}-nat"
    Project     = var.project_name
    Service     = "${var.project_name}-${var.env}-nat"
    Environment = var.env
    Terraform   = "true"
  }

  depends_on = [aws_internet_gateway.igw]
}


# Public Route Table
resource "aws_route_table" "public" {
  count  = var.create_vpc && length(local.public_subnet_cidrs) > 0 ? 1 : 0
  vpc_id = aws_vpc.vpc[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw[0].id
  }

  tags = {
    Name        = "${var.project_name}-${var.env}-public-route-table"
    Project     = var.project_name
    Service     = "${var.project_name}-${var.env}-public-route-table"
    Environment = var.env
    Terraform   = "true"
  }
}


# Single Private Route Table - Shared by all private subnets, pointing to single NAT Gateway
resource "aws_route_table" "private" {
  count  = var.create_vpc && length(local.private_subnet_cidrs) > 0 ? 1 : 0
  vpc_id = aws_vpc.vpc[0].id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat[0].id
  }

  tags = {
    Name        = "${var.project_name}-${var.env}-private-route-table"
    Project     = var.project_name
    Service     = "${var.project_name}-${var.env}-private-route-table"
    Environment = var.env
    Terraform   = "true"
  }
}


# Single Database Route Table - Shared by all database subnets (completely isolated, no internet access)
resource "aws_route_table" "database" {
  count  = var.create_vpc && length(local.database_subnet_cidrs) > 0 ? 1 : 0
  vpc_id = aws_vpc.vpc[0].id

  # No routes defined = complete isolation

  tags = {
    Name        = "${var.project_name}-${var.env}-database-route-table"
    Project     = var.project_name
    Service     = "${var.project_name}-${var.env}-database-route-table"
    Environment = var.env
    Terraform   = "true"
  }
}


# Public Route Table Association - All public subnets use the same shared route table
resource "aws_route_table_association" "public" {
  for_each       = var.create_vpc ? aws_subnet.public_subnet : {}
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public[0].id
}


# Private Route Table Association - All private subnets use the same shared route table
resource "aws_route_table_association" "private" {
  count          = var.create_vpc ? length(local.private_subnet_cidrs) : 0
  subnet_id      = values(aws_subnet.private_subnet)[count.index].id
  route_table_id = aws_route_table.private[0].id
}


# Database Route Table Association - All database subnets use the same shared isolated route table
resource "aws_route_table_association" "database" {
  count          = var.create_vpc ? length(local.database_subnet_cidrs) : 0
  subnet_id      = values(aws_subnet.database_subnet)[count.index].id
  route_table_id = aws_route_table.database[0].id
}


/*
for_each = toset(var.private_subnet_cidrs) 
    - if this is empty, it will not create any resources

each.key: This represents the key of the current item in the map or list.
each.value: This represents the value of the current item in the map or list.

The `for_each` loop allows us to create multiple resources dynamically.

- `each.key` refers to the index (position) of the current item in the list or the key in a map.
    - If we're iterating over a list, `each.key` is the position of the item in that list (e.g., 0 for the first item, 1 for the second item).
    - If we're iterating over a map, `each.key` is the name of the current item (e.g., "subnet1", "subnet2").

- `each.value` refers to the value of the current item.
    - For a list, `each.value` is the actual item in that list (e.g., "10.0.1.0/24").
    - For a map, `each.value` is the value associated with the key (e.g., the CIDR block like "10.0.1.0/24").

In this example, we are creating multiple subnets. `each.key` is used to get the position or name of the subnet, 
and `each.value` is used to get the CIDR block for each subnet.

*/