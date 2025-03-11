#############################################
# ITC RDS VPC Submodule
#############################################

#############################################
# Create a Secrets Manager Secret
#############################################
resource "aws_secretsmanager_secret" "allowed_postgres_cidrs" {
  name        = "${var.itc_database_prefix}-${var.env}-allowed-postgres-cidrs"
  description = "Stores a list of CIDR blocks allowed for PostgreSQL"
  tags = {
    Name = "${var.itc_database_prefix}-${var.env}-allowed-postgres-cidrs-secret"
  }
}

resource "aws_secretsmanager_secret_version" "allowed_postgres_cidrs_version" {
  secret_id     = aws_secretsmanager_secret.allowed_postgres_cidrs.id
  secret_string = jsonencode(var.allowed_postgres_cidrs)
  lifecycle {
    # Doesn’t overwrite on every plan/apply
    # when var.allowed_postgres_cidrs hasn't changed
    ignore_changes = [secret_string]
  }
}

#############################################
# Decode the stored JSON string into a list of CIDRs
#############################################
locals {
  postgres_cidrs_decoded = jsondecode(aws_secretsmanager_secret_version.allowed_postgres_cidrs_version.secret_string)
}

#############################################
# Create VPC
#############################################
resource "aws_vpc" "itc_database_vpc" {
  cidr_block           = "10.1.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name = "${var.itc_database_prefix}-vpc-new"
  }
}

resource "aws_internet_gateway" "itc_database_vpc_ig" {
  vpc_id = aws_vpc.itc_database_vpc.id
  tags = {
    Name = "Internet Gateway for ${var.itc_database_prefix}-vpc-new"
  }
}

resource "aws_db_subnet_group" "itc_database_vpc_subnet_group" {
  name       = "${var.itc_database_prefix}-new-subnet-group"
  subnet_ids = aws_subnet.itc_database_aws_subnet.*.id
  tags = {
    Name = "${var.itc_database_prefix}-new-subnet-group"
  }
}

#############################################
# Private subnets for secrets manager access
#############################################
resource "aws_subnet" "itc_database_private_subnet" {
  count             = length(var.private_subnet_cidrs)
  availability_zone = element(var.azs, count.index)
  vpc_id            = aws_vpc.itc_database_vpc.id
  cidr_block        = element(var.private_subnet_cidrs, count.index)
  map_public_ip_on_launch = false  # Ensure these remain private

  tags = {
    Name = "Private Subnet ${count.index + 1}"
  }
}

resource "aws_route_table" "itc_database_private_rt" {
  vpc_id = aws_vpc.itc_database_vpc.id
  tags = {
    Name = "Private Route Table"
  }
}

resource "aws_route_table_association" "itc_database_private_subnet_assoc" {
  count          = length(var.private_subnet_cidrs)
  subnet_id      = element(aws_subnet.itc_database_private_subnet[*].id, count.index)
  route_table_id = aws_route_table.itc_database_private_rt.id
}

#############################################
# Security group for VPC endpoints with basic rules
#############################################
resource "aws_security_group" "vpc_endpoints_sg" {
  name        = "${var.itc_database_prefix}-vpc-endpoints-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = aws_vpc.itc_database_vpc.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.itc_database_prefix}-vpc-endpoints-sg"
  }
}

resource "aws_security_group" "itc_database_vpc_sg" {
  name        = "${var.itc_database_prefix}-new-security-group"
  description = "Security group for RDS VPC"
  vpc_id      = aws_vpc.itc_database_vpc.id
  tags = {
    Name = "${var.itc_database_prefix}-new-security-group"
  }

  # Allow PostgreSQL access from your IP
  ingress {
    description = "Allow PostgreSQL access from specified IP addresses"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = local.postgres_cidrs_decoded
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_subnet" "itc_database_aws_subnet" {
  count             = length(var.public_subnet_cidrs)
  availability_zone = element(var.azs, count.index)
  vpc_id            = aws_vpc.itc_database_vpc.id
  cidr_block        = element(var.public_subnet_cidrs, count.index)

  map_public_ip_on_launch = true

  tags = {
    Name = "Public Subnet ${count.index + 1}"
  }
}

resource "aws_route_table" "itc_database_vpc_rt" {
  vpc_id = aws_vpc.itc_database_vpc.id
  tags = {
    Name = "${var.itc_database_prefix}-new-route-table"
  }

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.itc_database_vpc_ig.id
  }
}

resource "aws_route_table_association" "itc_database_vpc_public_subnet_assoc" {
  count          = length(var.public_subnet_cidrs)
  subnet_id      = element(aws_subnet.itc_database_aws_subnet[*].id, count.index)
  route_table_id = aws_route_table.itc_database_vpc_rt.id
}

#############################################
# VPC Endpoint to be able to call lambdas from the VPC
#############################################
resource "aws_vpc_endpoint" "itc_rds_vpc_endpoint_lambda_service" {
  count               = length(var.vpc_endpoint_services)
  private_dns_enabled = var.vpc_endpoint_services[count.index].type == "Interface" ? true : null
  service_name        = join(".", ["com.amazonaws", var.region, var.vpc_endpoint_services[count.index].svc])
  vpc_endpoint_type   = var.vpc_endpoint_services[count.index].type
  vpc_id              = aws_vpc.itc_database_vpc.id

  # Security groups only for Interface endpoints
  security_group_ids  = (
    var.vpc_endpoint_services[count.index].type == "Interface"
    ? [aws_security_group.vpc_endpoints_sg.id]
    : null
  )

  # Gateway endpoints need route table associations
  route_table_ids     = (
    var.vpc_endpoint_services[count.index].type == "Gateway"
    ? [aws_route_table.itc_database_private_rt.id, aws_route_table.itc_database_vpc_rt.id]
    : null
  )

  tags = {
    Name = "service-endpoint-for-${var.vpc_endpoint_services[count.index].svc}"
    Tech = "Service Endpoint"
    Srv  = "VPC"
  }
}

resource "aws_vpc_endpoint" "secretsmanager_endpoint" {
  service_name        = "com.amazonaws.${var.region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  vpc_id              = aws_vpc.itc_database_vpc.id
  subnet_ids          = aws_subnet.itc_database_private_subnet[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.itc_database_prefix}-secretsmanager-endpoint"
    Tech = "Service Endpoint"
    Srv  = "VPC"
  }
}


###################################
# NAT Gateway for private subnets
###################################
# Elastic IP for NAT Gateway
resource "aws_eip" "nat_eip" {
  domain = "vpc"
  tags = {
    Name = "${var.itc_database_prefix}-nat-eip"
  }
}

# NAT Gateway
resource "aws_nat_gateway" "nat_gateway" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.itc_database_aws_subnet[0].id  # Place in the first public subnet

  tags = {
    Name = "${var.itc_database_prefix}-nat-gateway"
  }

  depends_on = [aws_internet_gateway.itc_database_vpc_ig]
}

# Add route to private route table for NAT Gateway
resource "aws_route" "private_nat_gateway" {
  route_table_id         = aws_route_table.itc_database_private_rt.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.nat_gateway.id
}