# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC created by this module"
  value       = aws_vpc.this.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.this.cidr_block
}

# Subnet Outputs
output "public_subnet_ids" {
  description = "List of IDs of public subnets created by this module"
  value       = aws_subnet.public_subnets[*].id
}

output "private_app_subnet_ids" {
  description = "List of IDs of private application subnets created by this module"
  value       = aws_subnet.private_app_subnets[*].id
}

output "private_data_subnet_ids" {
  description = "List of IDs of private data subnets created by this module"
  value       = aws_subnet.private_data_subnets[*].id
}

# Gateway Outputs
output "internet_gateway_id" {
  description = "ID of the Internet Gateway created by this module"
  value       = aws_internet_gateway.this.id
}

output "nat_gateway_ids" {
  description = "List of IDs of NAT Gateways created by this module"
  value       = aws_nat_gateway.this[*].id
}

# Routing Outputs
output "public_route_table_id" {
  description = "ID of the public route table created by this module"
  value       = aws_route_table.public.id
}

output "private_route_table_ids" {
  description = "List of IDs of private route tables created by this module"
  value       = aws_route_table.private[*].id
}

# Security Group Outputs
output "alb_security_group_id" {
  description = "ID of the security group created for the Application Load Balancer"
  value       = length(aws_security_group.alb) > 0 ? aws_security_group.alb[0].id : null
}

output "app_security_group_id" {
  description = "ID of the security group created for the application tier"
  value       = length(aws_security_group.app) > 0 ? aws_security_group.app[0].id : null
}

output "db_security_group_id" {
  description = "ID of the security group created for the database tier"
  value       = length(aws_security_group.db) > 0 ? aws_security_group.db[0].id : null
}

output "cache_security_group_id" {
  description = "ID of the security group created for the cache tier"
  value       = length(aws_security_group.cache) > 0 ? aws_security_group.cache[0].id : null
}

# Flow Logs Outputs
output "vpc_flow_log_id" {
  description = "ID of the VPC Flow Log if created"
  value       = length(aws_flow_log.this) > 0 ? aws_flow_log.this[0].id : null
}

output "flow_log_destination_arn" {
  description = "ARN of the flow log destination (CloudWatch Log Group or S3 bucket)"
  value       = length(aws_flow_log.this) > 0 ? (var.flow_logs_destination_type == "s3" ? aws_s3_bucket.flow_logs[0].arn : aws_cloudwatch_log_group.flow_logs[0].arn) : null
}

# Availability Zone Output
output "availability_zones" {
  description = "List of availability zones used by the network module"
  value       = var.availability_zones
}