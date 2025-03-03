environment = "staging"
aws_region = "us-east-1"
project_name = "interaction-management"
enable_multi_az = true

# Network configuration
networking = {
  vpc_cidr                 = "10.0.0.0/16"
  public_subnets_cidr      = ["10.0.1.0/24", "10.0.2.0/24"]
  private_app_subnets_cidr = ["10.0.3.0/24", "10.0.4.0/24"]
  private_data_subnets_cidr = ["10.0.5.0/24", "10.0.6.0/24"]
  enable_nat_gateway       = true
  single_nat_gateway       = true  # Cost optimization: Use single NAT gateway in staging
  enable_vpn_gateway       = false
}

# Database configuration
database = {
  instance_class         = "db.t3.medium"  # Slightly smaller than production
  allocated_storage      = 50
  max_allocated_storage  = 200
  engine                 = "postgres"
  engine_version         = "15.3"
  multi_az               = true            # Enable multi-AZ for high availability testing
  backup_retention_period = 7
  deletion_protection    = true
  skip_final_snapshot    = false
  db_name                = "interaction_db"
  username               = "administrator"
  port                   = 5432
}

# Cache configuration
cache = {
  node_type                  = "cache.t3.medium"
  engine_version             = "7.0.12"
  num_cache_nodes            = 2
  parameter_group_name       = "default.redis7.0"
  port                       = 6379
  automatic_failover_enabled = true  # Enable for high availability testing
}

# Compute configuration
compute = {
  instance_type    = "t3.medium"  # Balance between performance and cost
  min_size         = 2            # Minimum for high availability
  max_size         = 4            # Allow scaling but capped lower than production
  desired_capacity = 2
  root_volume_size = 20
  root_volume_type = "gp3"
}

# Frontend service configuration
frontend_config = {
  container_port    = 80
  health_check_path = "/health"
  cpu               = 512         # Moderate CPU allocation
  memory            = 1024        # Moderate memory allocation
}

# Backend service configuration
backend_config = {
  container_port    = 5000
  health_check_path = "/api/health"
  cpu               = 512         # Moderate CPU allocation
  memory            = 1024        # Moderate memory allocation
}

# Domain and SSL configuration
domain_name = "staging.interaction-management.example.com"
enable_https = true

# Monitoring configuration
monitoring = {
  enable_detailed_monitoring = true
  create_dashboard           = true
  log_retention_days         = 30  # Moderate retention period
  alarm_email                = "staging-alerts@example.com"
  alarm_sms                  = null
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

# Tagging configuration
tags = {
  Project     = "InteractionManagement"
  Environment = "Staging"
  ManagedBy   = "Terraform"
  CostCenter  = "DevOps"
}

# Authentication configuration
auth0_domain = "staging-interactions.auth0.com"
auth0_client_id = "staging-client-id-placeholder"  # Use a placeholder in version control

# Static assets configuration
s3_assets_bucket_name = "staging-interaction-management-assets"

# Security configuration
enable_waf = true  # Enable WAF in staging to validate security configurations

# Auto-scaling configuration
cpu_scale_out_threshold = 70  # Balance between performance testing and cost
cpu_scale_in_threshold = 30
scale_out_cooldown = 300
scale_in_cooldown = 300