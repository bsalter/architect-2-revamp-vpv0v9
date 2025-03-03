# Core deployment variables
environment = "prod"
aws_region = "us-east-1"
project_name = "interaction-management"
enable_multi_az = true

# Network configuration for high availability
networking = {
  vpc_cidr                  = "10.0.0.0/16"
  public_subnets_cidr       = ["10.0.1.0/24", "10.0.2.0/24"]
  private_app_subnets_cidr  = ["10.0.3.0/24", "10.0.4.0/24"]
  private_data_subnets_cidr = ["10.0.5.0/24", "10.0.6.0/24"]
  enable_nat_gateway        = true
  single_nat_gateway        = false  # Use multiple NAT gateways for high availability
  enable_vpn_gateway        = false
}

# Production database configuration with high availability
database = {
  instance_class         = "db.t3.large"
  allocated_storage      = 100
  max_allocated_storage  = 500
  engine                 = "postgres"
  engine_version         = "15.3"
  multi_az               = true
  backup_retention_period = 30
  deletion_protection    = true
  skip_final_snapshot    = false
}

# Production cache configuration with multiple nodes
cache = {
  node_type            = "cache.t3.medium"
  engine_version       = "7.0.12"
  num_cache_nodes      = 2
  parameter_group_name = "default.redis7.0"
  port                 = 6379
  multi_az_enabled     = true
}

# Production compute configuration with increased capacity
compute = {
  instance_type    = "t3.medium"
  min_size         = 2
  max_size         = 8
  desired_capacity = 4
  root_volume_size = 30
  root_volume_type = "gp3"
}

# Frontend container configuration
frontend_config = {
  container_port    = 80
  health_check_path = "/health"
  cpu               = 1024
  memory            = 2048
}

# Backend container configuration
backend_config = {
  container_port    = 5000
  health_check_path = "/api/health"
  cpu               = 1024
  memory            = 2048
}

# Domain configuration
domain_name = "interaction-management.example.com"
enable_https = true

# Comprehensive monitoring configuration
monitoring = {
  enable_detailed_monitoring = true
  alarm_email                = "prod-alerts@example.com"
  alarm_sms                  = "+15551234567"
  retention_in_days          = 90
  create_dashboard           = true
  alert_thresholds = {
    cpu_utilization_warning     = 70
    cpu_utilization_critical    = 85
    memory_usage_warning        = 70
    memory_usage_critical       = 85
    api_response_time_warning   = 500
    api_response_time_critical  = 2000
    error_rate_warning          = 1
    error_rate_critical         = 5
    database_query_time_warning = 300
    database_query_time_critical = 1000
    cache_hit_ratio_warning     = 80
    cache_hit_ratio_critical    = 60
  }
}

# Resource tags for identification and cost tracking
tags = {
  Project     = "InteractionManagement"
  Environment = "Production"
  ManagedBy   = "Terraform"
  CostCenter  = "Operations"
}

# Authentication configuration
auth0_domain = "interactions.auth0.com"
auth0_client_id = "production-client-id-placeholder"

# Static assets configuration
s3_assets_bucket_name = "interaction-management-assets"

# Security configuration
enable_waf = true

# Auto-scaling configuration
cpu_scale_out_threshold = 60  # Lower threshold for quicker scaling in production
cpu_scale_in_threshold = 30   # Optimize resource usage in production
scale_out_cooldown = 180      # Shorter cooldown to respond quickly to traffic spikes
scale_in_cooldown = 300       # Standard cooldown for scaling in activities