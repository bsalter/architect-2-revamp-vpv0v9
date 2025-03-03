# Networking module for the Interaction Management System
# Creates a multi-tier VPC architecture with public and private subnets,
# internet connectivity, and security groups

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

locals {
  name_prefix             = var.environment != "" ? "${var.environment}-" : ""
  common_tags             = merge(var.tags, { Environment = var.environment })
  nat_gateway_count       = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0
  public_subnet_count     = length(var.public_subnets_cidr) > 0 ? length(var.public_subnets_cidr) : 0
  private_app_subnet_count = length(var.private_app_subnets_cidr) > 0 ? length(var.private_app_subnets_cidr) : 0
  private_data_subnet_count = length(var.private_data_subnets_cidr) > 0 ? length(var.private_data_subnets_cidr) : 0
}

# Create the VPC
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support
  tags                 = merge(local.common_tags, { Name = "${local.name_prefix}vpc" })
}

# Create public subnets
resource "aws_subnet" "public_subnets" {
  count                   = local.public_subnet_count
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnets_cidr[count.index]
  availability_zone       = var.availability_zones[count.index % length(var.availability_zones)]
  map_public_ip_on_launch = true
  tags                    = merge(local.common_tags, { Name = "${local.name_prefix}public-subnet-${count.index + 1}" })
}

# Create private application subnets
resource "aws_subnet" "private_app_subnets" {
  count                   = local.private_app_subnet_count
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.private_app_subnets_cidr[count.index]
  availability_zone       = var.availability_zones[count.index % length(var.availability_zones)]
  map_public_ip_on_launch = false
  tags                    = merge(local.common_tags, { Name = "${local.name_prefix}private-app-subnet-${count.index + 1}" })
}

# Create private data subnets
resource "aws_subnet" "private_data_subnets" {
  count                   = local.private_data_subnet_count
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.private_data_subnets_cidr[count.index]
  availability_zone       = var.availability_zones[count.index % length(var.availability_zones)]
  map_public_ip_on_launch = false
  tags                    = merge(local.common_tags, { Name = "${local.name_prefix}private-data-subnet-${count.index + 1}" })
}

# Create internet gateway for public internet access
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = merge(local.common_tags, { Name = "${local.name_prefix}igw" })
}

# Create elastic IPs for NAT gateways
resource "aws_eip" "nat" {
  count = local.nat_gateway_count
  vpc   = true
  tags  = merge(local.common_tags, { Name = "${local.name_prefix}nat-eip-${count.index + 1}" })
}

# Create NAT gateways for private subnet outbound internet access
resource "aws_nat_gateway" "this" {
  count         = local.nat_gateway_count
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public_subnets[count.index % local.public_subnet_count].id
  tags          = merge(local.common_tags, { Name = "${local.name_prefix}nat-gw-${count.index + 1}" })
  depends_on    = [aws_internet_gateway.this]
}

# Create route table for public subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }
  tags = merge(local.common_tags, { Name = "${local.name_prefix}public-rt" })
}

# Create route tables for private subnets
resource "aws_route_table" "private" {
  count  = var.single_nat_gateway ? 1 : local.nat_gateway_count
  vpc_id = aws_vpc.this.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = var.single_nat_gateway ? aws_nat_gateway.this[0].id : aws_nat_gateway.this[count.index].id
  }
  tags = merge(local.common_tags, { Name = "${local.name_prefix}private-rt-${count.index + 1}" })
}

# Associate public subnets with public route table
resource "aws_route_table_association" "public" {
  count          = local.public_subnet_count
  subnet_id      = aws_subnet.public_subnets[count.index].id
  route_table_id = aws_route_table.public.id
}

# Associate private app subnets with private route tables
resource "aws_route_table_association" "private_app" {
  count          = local.private_app_subnet_count
  subnet_id      = aws_subnet.private_app_subnets[count.index].id
  route_table_id = var.single_nat_gateway ? aws_route_table.private[0].id : aws_route_table.private[count.index % length(aws_route_table.private)].id
}

# Associate private data subnets with private route tables
resource "aws_route_table_association" "private_data" {
  count          = local.private_data_subnet_count
  subnet_id      = aws_subnet.private_data_subnets[count.index].id
  route_table_id = var.single_nat_gateway ? aws_route_table.private[0].id : aws_route_table.private[count.index % length(aws_route_table.private)].id
}

# Create IAM role for VPC flow logs
resource "aws_iam_role" "flow_log_role" {
  count = var.enable_flow_logs ? 1 : 0
  name  = "${local.name_prefix}flow-log-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(local.common_tags, { Name = "${local.name_prefix}flow-log-role" })
}

# Create IAM policy for flow logs role
resource "aws_iam_role_policy" "flow_log_policy" {
  count = var.enable_flow_logs ? 1 : 0
  name  = "${local.name_prefix}flow-log-policy"
  role  = aws_iam_role.flow_log_role[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# Create CloudWatch log group for flow logs
resource "aws_cloudwatch_log_group" "flow_logs" {
  count             = var.enable_flow_logs && var.flow_logs_destination_type == "cloud-watch-logs" ? 1 : 0
  name              = "/aws/vpc-flow-logs/${local.name_prefix}vpc"
  retention_in_days = 30
  tags              = merge(local.common_tags, { Name = "${local.name_prefix}vpc-flow-logs" })
}

# Create a random string for unique S3 bucket naming
resource "random_string" "s3_suffix" {
  count   = var.enable_flow_logs && var.flow_logs_destination_type == "s3" ? 1 : 0
  length  = 8
  special = false
  upper   = false
}

# Create S3 bucket for flow logs
resource "aws_s3_bucket" "flow_logs" {
  count  = var.enable_flow_logs && var.flow_logs_destination_type == "s3" ? 1 : 0
  bucket = "${local.name_prefix}vpc-flow-logs-${random_string.s3_suffix[0].result}"
  tags   = merge(local.common_tags, { Name = "${local.name_prefix}vpc-flow-logs" })
}

# Enable S3 bucket server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "flow_logs" {
  count  = var.enable_flow_logs && var.flow_logs_destination_type == "s3" ? 1 : 0
  bucket = aws_s3_bucket.flow_logs[0].id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access to S3 bucket
resource "aws_s3_bucket_public_access_block" "flow_logs" {
  count                   = var.enable_flow_logs && var.flow_logs_destination_type == "s3" ? 1 : 0
  bucket                  = aws_s3_bucket.flow_logs[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Create VPC flow logs
resource "aws_flow_log" "this" {
  count                = var.enable_flow_logs ? 1 : 0
  vpc_id               = aws_vpc.this.id
  traffic_type         = var.flow_logs_traffic_type
  iam_role_arn         = aws_iam_role.flow_log_role[0].arn
  log_destination_type = var.flow_logs_destination_type
  log_destination      = var.flow_logs_destination_type == "s3" ? aws_s3_bucket.flow_logs[0].arn : aws_cloudwatch_log_group.flow_logs[0].arn
  tags                 = merge(local.common_tags, { Name = "${local.name_prefix}vpc-flow-logs" })
}

# Create security group for ALB
resource "aws_security_group" "alb" {
  count       = var.create_alb_security_group ? 1 : 0
  name        = "${local.name_prefix}alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.this.id
  
  # Allow HTTPS ingress from specified CIDR blocks
  ingress {
    from_port   = var.alb_ingress_port
    to_port     = var.alb_ingress_port
    protocol    = "tcp"
    cidr_blocks = var.alb_ingress_cidr_blocks
    description = "Allow inbound traffic to ALB"
  }
  
  # Allow HTTP ingress from specified CIDR blocks
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.alb_ingress_cidr_blocks
    description = "Allow HTTP traffic to ALB"
  }
  
  # Allow all egress
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = merge(local.common_tags, { Name = "${local.name_prefix}alb-sg" })
}

# Create security group for application tier
resource "aws_security_group" "app" {
  count       = var.create_app_security_group ? 1 : 0
  name        = "${local.name_prefix}app-sg"
  description = "Security group for application tier"
  vpc_id      = aws_vpc.this.id
  
  # Allow ingress from ALB security group
  ingress {
    from_port       = var.app_ingress_port
    to_port         = var.app_ingress_port
    protocol        = "tcp"
    security_groups = var.create_alb_security_group ? [aws_security_group.alb[0].id] : []
    description     = "Allow inbound traffic from ALB"
  }
  
  # Allow all egress
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = merge(local.common_tags, { Name = "${local.name_prefix}app-sg" })
}

# Create security group for database tier
resource "aws_security_group" "db" {
  count       = var.create_db_security_group ? 1 : 0
  name        = "${local.name_prefix}db-sg"
  description = "Security group for database tier"
  vpc_id      = aws_vpc.this.id
  
  # Allow ingress from app security group
  ingress {
    from_port       = var.db_port
    to_port         = var.db_port
    protocol        = "tcp"
    security_groups = var.create_app_security_group ? [aws_security_group.app[0].id] : []
    description     = "Allow inbound traffic from application tier"
  }
  
  # Allow all egress
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = merge(local.common_tags, { Name = "${local.name_prefix}db-sg" })
}

# Create security group for cache tier
resource "aws_security_group" "cache" {
  count       = var.create_cache_security_group ? 1 : 0
  name        = "${local.name_prefix}cache-sg"
  description = "Security group for cache tier"
  vpc_id      = aws_vpc.this.id
  
  # Allow ingress from app security group
  ingress {
    from_port       = var.cache_port
    to_port         = var.cache_port
    protocol        = "tcp"
    security_groups = var.create_app_security_group ? [aws_security_group.app[0].id] : []
    description     = "Allow inbound traffic from application tier"
  }
  
  # Allow all egress
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = merge(local.common_tags, { Name = "${local.name_prefix}cache-sg" })
}

# Define outputs that will be used by other modules
output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.this.id
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC"
  value       = aws_vpc.this.cidr_block
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets"
  value       = aws_subnet.public_subnets[*].id
}

output "private_app_subnet_ids" {
  description = "List of IDs of private application subnets"
  value       = aws_subnet.private_app_subnets[*].id
}

output "private_data_subnet_ids" {
  description = "List of IDs of private data subnets"
  value       = aws_subnet.private_data_subnets[*].id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.this[*].id
}

output "internet_gateway_id" {
  description = "ID of the internet gateway"
  value       = aws_internet_gateway.this.id
}

output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = var.create_alb_security_group ? aws_security_group.alb[0].id : null
}

output "app_security_group_id" {
  description = "ID of the application security group"
  value       = var.create_app_security_group ? aws_security_group.app[0].id : null
}

output "db_security_group_id" {
  description = "ID of the database security group"
  value       = var.create_db_security_group ? aws_security_group.db[0].id : null
}

output "cache_security_group_id" {
  description = "ID of the cache security group"
  value       = var.create_cache_security_group ? aws_security_group.cache[0].id : null
}

output "public_route_table_id" {
  description = "ID of the public route table"
  value       = aws_route_table.public.id
}

output "private_route_table_ids" {
  description = "List of IDs of private route tables"
  value       = aws_route_table.private[*].id
}

output "vpc_flow_log_id" {
  description = "ID of the VPC Flow Log"
  value       = var.enable_flow_logs ? aws_flow_log.this[0].id : null
}