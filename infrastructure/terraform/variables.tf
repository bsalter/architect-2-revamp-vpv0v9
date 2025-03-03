# Core deployment variables
variable "environment" {
  description = "Deployment environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "The environment value must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region where resources will be deployed"
  type        = string
  default     = "us-east-1"
  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", var.aws_region))
    error_message = "The aws_region value must be a valid AWS region, e.g., us-east-1."
  }
}

variable "project_name" {
  description = "Name of the project used for resource naming and tagging"
  type        = string
  default     = "interaction-management"
  validation {
    condition     = can(regex("^[a-zA-Z0-9-_]+$", var.project_name))
    error_message = "The project_name value must comply with AWS naming restrictions (only alphanumeric, hyphens, and underscores)."
  }
}

variable "enable_multi_az" {
  description = "Whether to enable Multi-AZ deployment for high availability"
  type        = bool
  default     = false
}

# Network configuration
variable "networking" {
  description = "Networking configuration for VPC, subnets, and network features"
  type = object({
    vpc_cidr                 = string
    public_subnets_cidr      = list(string)
    private_app_subnets_cidr = list(string)
    private_data_subnets_cidr = list(string)
    enable_nat_gateway       = bool
    single_nat_gateway       = bool
    enable_vpn_gateway       = bool
  })
  default = {
    vpc_cidr                 = "10.0.0.0/16"
    public_subnets_cidr      = ["10.0.1.0/24", "10.0.2.0/24"]
    private_app_subnets_cidr = ["10.0.3.0/24", "10.0.4.0/24"]
    private_data_subnets_cidr = ["10.0.5.0/24", "10.0.6.0/24"]
    enable_nat_gateway       = true
    single_nat_gateway       = true
    enable_vpn_gateway       = false
  }
  validation {
    condition     = can(cidrnetmask(var.networking.vpc_cidr))
    error_message = "The VPC CIDR block must be a valid CIDR notation."
  }
}

# Database configuration
variable "database" {
  description = "Database configuration for PostgreSQL RDS instance"
  type = object({
    instance_class         = string
    allocated_storage      = number
    max_allocated_storage  = number
    engine                 = string
    engine_version         = string
    backup_retention_period = number
    deletion_protection    = bool
    skip_final_snapshot    = bool
    db_name                = string
    username               = string
    port                   = number
  })
  default = {
    instance_class         = "db.t3.large"
    allocated_storage      = 20
    max_allocated_storage  = 100
    engine                 = "postgres"
    engine_version         = "15.3"
    backup_retention_period = 7
    deletion_protection    = true
    skip_final_snapshot    = false
    db_name                = "interaction_db"
    username               = "administrator"
    port                   = 5432
  }
  validation {
    condition     = can(regex("^db\\.", var.database.instance_class))
    error_message = "The database instance_class must be a valid RDS instance type, starting with 'db.'."
  }
}

# Cache configuration
variable "cache" {
  description = "Cache configuration for Redis ElastiCache"
  type = object({
    node_type                  = string
    engine_version             = string
    num_cache_nodes            = number
    parameter_group_name       = string
    port                       = number
    automatic_failover_enabled = bool
  })
  default = {
    node_type                  = "cache.t3.medium"
    engine_version             = "7.0.12"
    num_cache_nodes            = 2
    parameter_group_name       = "default.redis7.0"
    port                       = 6379
    automatic_failover_enabled = true
  }
  validation {
    condition     = can(regex("^cache\\.", var.cache.node_type))
    error_message = "The cache node_type must be a valid ElastiCache instance type, starting with 'cache.'."
  }
}

# Compute configuration
variable "compute" {
  description = "Compute configuration for EC2/ECS instances and auto-scaling"
  type = object({
    instance_type    = string
    min_size         = number
    max_size         = number
    desired_capacity = number
    root_volume_size = number
    root_volume_type = string
  })
  default = {
    instance_type    = "t3.medium"
    min_size         = 2
    max_size         = 4
    desired_capacity = 2
    root_volume_size = 20
    root_volume_type = "gp3"
  }
  validation {
    condition     = contains(["t3.small", "t3.medium", "t3.large", "m5.large", "m5.xlarge", "c5.large", "c5.xlarge"], var.compute.instance_type)
    error_message = "The compute instance_type must be a valid EC2 instance type suitable for the application."
  }
}

# Frontend service configuration
variable "frontend_config" {
  description = "Frontend service configuration for container settings"
  type = object({
    container_port    = number
    health_check_path = string
    cpu               = number
    memory            = number
  })
  default = {
    container_port    = 80
    health_check_path = "/health"
    cpu               = 256
    memory            = 512
  }
  validation {
    condition     = var.frontend_config.container_port > 0 && var.frontend_config.container_port < 65536
    error_message = "The frontend container_port must be between 1 and 65535."
  }
}

# Backend service configuration
variable "backend_config" {
  description = "Backend service configuration for container settings"
  type = object({
    container_port    = number
    health_check_path = string
    cpu               = number
    memory            = number
  })
  default = {
    container_port    = 5000
    health_check_path = "/api/health"
    cpu               = 512
    memory            = 1024
  }
  validation {
    condition     = var.backend_config.container_port > 0 && var.backend_config.container_port < 65536
    error_message = "The backend container_port must be between 1 and 65535."
  }
}

# Domain and SSL configuration
variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = null
  validation {
    condition     = var.domain_name == null ? true : can(regex("^([a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]\\.)+[a-zA-Z]{2,}$", var.domain_name))
    error_message = "If provided, the domain_name must be a valid domain name format."
  }
}

# Monitoring configuration
variable "monitoring" {
  description = "Monitoring configuration for CloudWatch resources"
  type = object({
    enable_detailed_monitoring = bool
    create_dashboard           = bool
    log_retention_days         = number
    alarm_email                = string
    alarm_sms                  = string
    alert_thresholds = object({
      cpu_utilization_warning     = number
      cpu_utilization_critical    = number
      memory_usage_warning        = number
      memory_usage_critical       = number
      api_response_time_warning   = number
      api_response_time_critical  = number
      error_rate_warning          = number
      error_rate_critical         = number
      database_query_time_warning = number
      database_query_time_critical = number
      cache_hit_ratio_warning     = number
      cache_hit_ratio_critical    = number
    })
  })
  default = {
    enable_detailed_monitoring = true
    create_dashboard           = true
    log_retention_days         = 30
    alarm_email                = null
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
  validation {
    condition     = var.monitoring.alarm_email == null ? true : can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.monitoring.alarm_email))
    error_message = "If provided, the alarm_email must be a valid email format."
  }
}

# Tagging configuration
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project    = "InteractionManagement"
    ManagedBy  = "Terraform"
  }
}

# Authentication configuration
variable "auth0_domain" {
  description = "Auth0 tenant domain for authentication"
  type        = string
  default     = null
  validation {
    condition     = var.auth0_domain == null ? true : can(regex("^[a-zA-Z0-9.-]+\\.auth0\\.com$", var.auth0_domain))
    error_message = "If provided, the auth0_domain must be a valid Auth0 domain format."
  }
}

# Static assets configuration
variable "s3_assets_bucket_name" {
  description = "S3 bucket name for static assets"
  type        = string
  default     = null
  validation {
    condition     = var.s3_assets_bucket_name == null ? true : can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.s3_assets_bucket_name))
    error_message = "If provided, the s3_assets_bucket_name must follow S3 bucket naming conventions."
  }
}

# Security configuration
variable "enable_waf" {
  description = "Whether to enable WAF for web application protection"
  type        = bool
  default     = false
}

# Auto-scaling configuration
variable "cpu_scale_out_threshold" {
  description = "CPU utilization threshold percentage to trigger scale out"
  type        = number
  default     = 70
  validation {
    condition     = var.cpu_scale_out_threshold >= 0 && var.cpu_scale_out_threshold <= 100
    error_message = "The cpu_scale_out_threshold must be between 0 and 100."
  }
}

variable "cpu_scale_in_threshold" {
  description = "CPU utilization threshold percentage to trigger scale in"
  type        = number
  default     = 30
  validation {
    condition     = var.cpu_scale_in_threshold >= 0 && var.cpu_scale_in_threshold <= 100
    error_message = "The cpu_scale_in_threshold must be between 0 and 100."
  }
}

variable "scale_out_cooldown" {
  description = "Cooldown period in seconds after scaling out"
  type        = number
  default     = 300
  validation {
    condition     = var.scale_out_cooldown >= 0
    error_message = "The scale_out_cooldown must be greater than or equal to 0."
  }
}

variable "scale_in_cooldown" {
  description = "Cooldown period in seconds after scaling in"
  type        = number
  default     = 300
  validation {
    condition     = var.scale_in_cooldown >= 0
    error_message = "The scale_in_cooldown must be greater than or equal to 0."
  }
}