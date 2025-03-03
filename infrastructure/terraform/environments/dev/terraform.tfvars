# Core deployment variables
environment         = "dev"
aws_region          = "us-east-1"
project_name        = "interaction-management"
enable_multi_az     = false

# Network configuration
networking = {
  vpc_cidr                 = "10.0.0.0/16"
  public_subnets_cidr      = ["10.0.1.0/24", "10.0.2.0/24"]
  private_app_subnets_cidr = ["10.0.3.0/24", "10.0.4.0/24"]
  private_data_subnets_cidr = ["10.0.5.0/24", "10.0.6.0/24"]
  enable_nat_gateway       = true
  single_nat_gateway       = true
  enable_vpn_gateway       = false
}

# Database configuration (smaller instance for dev)
database = {
  instance_class         = "db.t3.small"
  allocated_storage      = 20
  max_allocated_storage  = 50
  engine                 = "postgres"
  engine_version         = "15.3"
  multi_az               = false
  backup_retention_period = 3
  deletion_protection    = false
  skip_final_snapshot    = true
}

# Cache configuration (single node for dev)
cache = {
  node_type              = "cache.t3.small"
  engine_version         = "7.0.12"
  num_cache_nodes        = 1
  parameter_group_name   = "default.redis7.0"
  port                   = 6379
  multi_az_enabled       = false
}

# Compute configuration (minimal resources for dev)
compute = {
  instance_type          = "t3.small"
  min_size               = 1
  max_size               = 2
  desired_capacity       = 1
  root_volume_size       = 20
  root_volume_type       = "gp3"
}

# Frontend service configuration
frontend_config = {
  container_port         = 80
  health_check_path      = "/health"
  cpu                    = 256
  memory                 = 512
}

# Backend service configuration
backend_config = {
  container_port         = 5000
  health_check_path      = "/api/health"
  cpu                    = 256
  memory                 = 512
}

# Domain and SSL configuration
domain_name              = "dev.interaction-management.example.com"
enable_https             = true

# Monitoring configuration (reduced for dev)
monitoring = {
  enable_detailed_monitoring = false
  alarm_email                = "dev-alerts@example.com"
  alarm_sms                  = null
  retention_in_days          = 7
  create_dashboard           = true
}

# Tagging configuration
tags = {
  Project                = "InteractionManagement"
  Environment            = "Development"
  ManagedBy              = "Terraform"
  CostCenter             = "DevOps"
}

# Authentication configuration
auth0_domain            = "dev-interactions.auth0.com"
auth0_client_id         = "dev-client-id-placeholder"

# Static assets configuration
s3_assets_bucket_name   = "dev-interaction-management-assets"

# Security configuration
enable_waf              = false

# Auto-scaling configuration
cpu_scale_out_threshold = 80
cpu_scale_in_threshold  = 30
scale_out_cooldown      = 300
scale_in_cooldown       = 300