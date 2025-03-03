# AWS provider version ~> 4.0 is used in this project for infrastructure resources

# Network Outputs
output "vpc_id" {
  description = "The ID of the VPC where all resources are deployed"
  value       = module.networking.vpc_id
}

output "network_details" {
  description = "Network infrastructure details including subnet IDs and CIDR blocks"
  value = {
    vpc_id            = module.networking.vpc_id
    public_subnet_ids = module.networking.public_subnet_ids
    private_app_subnet_ids = module.networking.private_app_subnet_ids
    private_data_subnet_ids = module.networking.private_data_subnet_ids
    vpc_cidr_block    = module.networking.vpc_cidr_block
    availability_zones = module.networking.availability_zones
    nat_gateway_ips   = module.networking.nat_gateway_ips
  }
}

# Application Endpoints
output "application_endpoint" {
  description = "The main application endpoint for accessing the Interaction Management System"
  value       = module.compute.application_url
}

output "api_endpoint" {
  description = "API endpoint for the backend services"
  value       = coalesce(var.custom_domain_api, module.compute.api_load_balancer_dns)
}

# Database Outputs
output "database_connection" {
  description = "Database connection information (without sensitive credentials)"
  value = {
    host          = module.database.rds_instance_address
    port          = module.database.rds_instance_port
    database_name = module.database.rds_database_name
    engine        = "postgresql"
    engine_version = module.database.rds_engine_version
    multi_az      = module.database.rds_multi_az
  }
}

output "redis_connection" {
  description = "Redis cache connection information"
  value = {
    primary_endpoint = module.database.redis_primary_endpoint
    reader_endpoint  = module.database.redis_reader_endpoint
    port             = module.database.redis_port
    engine_version   = module.database.redis_engine_version
    num_cache_nodes  = module.database.redis_num_cache_nodes
  }
}

# Monitoring Outputs
output "cloudwatch_dashboard_url" {
  description = "URL to access the CloudWatch dashboard for monitoring the system"
  value       = module.monitoring.dashboard_url
}

# Storage Outputs
output "s3_assets_bucket" {
  description = "The S3 bucket name storing static assets for the application"
  value       = aws_s3_bucket.static_assets.bucket
}

output "cloudfront_distribution_domain" {
  description = "The CloudFront distribution domain name for serving static assets"
  value       = aws_cloudfront_distribution.static_assets_cdn.domain_name
}

# Security Outputs
output "security_details" {
  description = "Security resource identifiers for reference (non-sensitive)"
  value = {
    role_arns = {
      ecs_task_execution = module.security.ecs_task_execution_role_arn
      ecs_task           = module.security.ecs_task_role_arn
      lambda             = module.security.lambda_role_arn
    }
    security_group_ids = {
      alb         = module.security.alb_security_group_id
      app         = module.security.app_security_group_id
      db          = module.security.db_security_group_id
      redis       = module.security.redis_security_group_id
    }
    waf_web_acl_id = module.security.waf_web_acl_id
    kms_key_id     = module.security.kms_key_id
  }
}

# Environment Outputs
output "environment_details" {
  description = "Details about the environment configuration"
  value = {
    name        = var.environment
    region      = var.aws_region
    multi_az    = var.multi_az_deployment
    account_id  = data.aws_caller_identity.current.account_id
    tags        = var.default_tags
  }
}

# Container Orchestration
output "ecs_cluster_name" {
  description = "The name of the ECS cluster running the application containers"
  value       = module.compute.ecs_cluster_name
}

# Notifications
output "alarm_topic_arns" {
  description = "ARNs of SNS topics used for different types of alerts"
  value = {
    critical = module.monitoring.critical_alarm_topic_arn
    warning  = module.monitoring.warning_alarm_topic_arn
    info     = module.monitoring.info_alarm_topic_arn
  }
}