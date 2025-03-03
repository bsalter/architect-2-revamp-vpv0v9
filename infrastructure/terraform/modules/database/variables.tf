#------------------------------------------------------------------------------
# General variables
#------------------------------------------------------------------------------

variable "environment" {
  description = "Environment identifier (dev, staging, prod) used for resource naming and configuration"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
  
  validation {
    condition     = length(var.project_name) > 0
    error_message = "Project name cannot be empty."
  }
}

#------------------------------------------------------------------------------
# Network and security variables
#------------------------------------------------------------------------------

variable "vpc_id" {
  description = "ID of the VPC where database resources will be created"
  type        = string
}

variable "private_data_subnet_ids" {
  description = "List of private data subnet IDs where database resources will be deployed"
  type        = list(string)
  
  validation {
    condition     = length(var.private_data_subnet_ids) >= 2
    error_message = "At least two subnet IDs are required for high availability deployment."
  }
}

variable "db_security_group_id" {
  description = "ID of the security group for database access"
  type        = string
}

variable "cache_security_group_id" {
  description = "ID of the security group for cache access"
  type        = string
}

variable "kms_key_id" {
  description = "KMS key ID used for database encryption"
  type        = string
}

#------------------------------------------------------------------------------
# PostgreSQL database configuration
#------------------------------------------------------------------------------

variable "database" {
  description = "PostgreSQL database configuration object"
  type = object({
    instance_class                      = string
    allocated_storage                   = number
    max_allocated_storage               = optional(number)
    engine                              = string
    engine_version                      = string
    backup_retention_period             = number
    backup_window                       = optional(string)
    maintenance_window                  = optional(string)
    deletion_protection                 = bool
    skip_final_snapshot                 = bool
    db_name                             = string
    username                            = string
    port                                = number
    performance_insights_enabled        = optional(bool)
    performance_insights_retention_period = optional(number)
    parameters                          = optional(map(string))
  })
  
  default = {
    instance_class                      = "db.t3.large"
    allocated_storage                   = 100
    max_allocated_storage               = 500
    engine                              = "postgres"
    engine_version                      = "15.3"
    backup_retention_period             = 30
    backup_window                       = "03:00-04:00"
    maintenance_window                  = "Mon:04:00-Mon:05:00"
    deletion_protection                 = true
    skip_final_snapshot                 = false
    db_name                             = "interaction_db"
    username                            = "administrator"
    port                                = 5432
    performance_insights_enabled        = true
    performance_insights_retention_period = 7
    parameters = {
      "shared_buffers"                  = "256MB"
      "max_connections"                 = "100"
      "work_mem"                        = "4MB"
      "maintenance_work_mem"            = "64MB"
      "checkpoint_timeout"              = "300"
      "checkpoint_completion_target"    = "0.8"
      "effective_cache_size"            = "1GB"
      "log_min_duration_statement"      = "200"
    }
  }
  
  validation {
    condition     = var.database.engine == "postgres"
    error_message = "The engine must be set to 'postgres'."
  }
  
  validation {
    condition     = var.database.allocated_storage >= 20
    error_message = "Allocated storage must be at least 20GB for PostgreSQL."
  }
}

#------------------------------------------------------------------------------
# Redis cache configuration
#------------------------------------------------------------------------------

variable "cache" {
  description = "Redis cache configuration object"
  type = object({
    node_type                     = string
    engine_version                = string
    num_cache_nodes               = number
    parameter_group_name          = string
    port                          = number
    automatic_failover_enabled    = optional(bool)
    multi_az_enabled              = optional(bool)
    snapshot_retention_limit      = optional(number)
    snapshot_window               = optional(string)
    maintenance_window            = optional(string)
    at_rest_encryption_enabled    = optional(bool)
    transit_encryption_enabled    = optional(bool)
  })
  
  default = {
    node_type                     = "cache.t3.medium"
    engine_version                = "7.0.12"
    num_cache_nodes               = 2
    parameter_group_name          = "default.redis7.0"
    port                          = 6379
    automatic_failover_enabled    = true
    multi_az_enabled              = true
    snapshot_retention_limit      = 7
    snapshot_window               = "05:00-06:00"
    maintenance_window            = "sun:06:00-sun:07:00"
    at_rest_encryption_enabled    = true
    transit_encryption_enabled    = true
  }
  
  validation {
    condition     = startswith(var.cache.parameter_group_name, "default.redis")
    error_message = "Parameter group name should be a valid Redis parameter group."
  }
}

#------------------------------------------------------------------------------
# Operational settings
#------------------------------------------------------------------------------

variable "enable_multi_az" {
  description = "Whether to enable Multi-AZ deployment for high availability"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to all database resources"
  type        = map(string)
  default     = {}
}