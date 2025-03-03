# ------------------------------------------------------------------------------
# COMPUTE MODULE VARIABLES
# Defines configuration for AWS compute resources for the Interaction Management System
# ------------------------------------------------------------------------------

# Project and Environment Variables
variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
}

variable "environment" {
  description = "Deployment environment identifier used for resource naming and configuration"
  type        = string
}

# Network Configuration
variable "vpc_id" {
  description = "VPC ID where compute resources will be deployed"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for load balancer deployment"
  type        = list(string)
}

variable "private_app_subnet_ids" {
  description = "List of private application subnet IDs for compute resources deployment"
  type        = list(string)
}

# Security Groups
variable "alb_security_group_id" {
  description = "Security group ID for the application load balancer"
  type        = string
}

variable "app_security_group_id" {
  description = "Security group ID for the application servers"
  type        = string
}

# Compute Configuration
variable "instance_type" {
  description = "EC2 instance type for compute resources"
  type        = string
  default     = "t3.medium"
  
  validation {
    condition     = can(regex("^[a-z][0-9][.][a-z]+$", var.instance_type))
    error_message = "The instance_type must be a valid EC2 instance type, e.g., t3.medium."
  }
}

variable "frontend_config" {
  description = "Configuration object for the frontend service"
  type = object({
    container_port     = number
    health_check_path  = string
    image              = string
    cpu                = number
    memory             = number
    desired_count      = number
  })
  default = {
    container_port     = 80
    health_check_path  = "/"
    image              = "nginx:latest"
    cpu                = 256
    memory             = 512
    desired_count      = 2
  }
}

variable "backend_config" {
  description = "Configuration object for the backend service"
  type = object({
    container_port     = number
    health_check_path  = string
    image              = string
    cpu                = number
    memory             = number
    desired_count      = number
  })
  default = {
    container_port     = 5000
    health_check_path  = "/api/health"
    image              = "python:3.11-slim"
    cpu                = 512
    memory             = 1024
    desired_count      = 2
  }
}

# Auto Scaling Configuration
variable "min_size" {
  description = "Minimum number of instances in the auto-scaling group"
  type        = number
  default     = 2
  
  validation {
    condition     = var.min_size >= 1
    error_message = "The min_size must be at least 1."
  }
}

variable "max_size" {
  description = "Maximum number of instances in the auto-scaling group"
  type        = number
  default     = 4
  
  validation {
    condition     = var.max_size >= 2
    error_message = "The max_size must be at least 2 for high availability."
  }
}

variable "desired_capacity" {
  description = "Desired number of instances in the auto-scaling group"
  type        = number
  default     = 2
}

# Load Balancer Configuration
variable "enable_https" {
  description = "Whether to enable HTTPS for the load balancer"
  type        = bool
  default     = true
}

variable "certificate_arn" {
  description = "ARN of the ACM certificate for HTTPS (required if enable_https is true)"
  type        = string
  default     = null
}

variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = null
  
  validation {
    condition     = var.domain_name == null ? true : can(regex("^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\\.)+[a-zA-Z]{2,}$", var.domain_name))
    error_message = "The domain_name must be a valid domain name."
  }
}

# Auto Scaling Policies
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
    condition     = var.scale_out_cooldown > 0
    error_message = "The scale_out_cooldown must be greater than 0."
  }
}

variable "scale_in_cooldown" {
  description = "Cooldown period in seconds after scaling in"
  type        = number
  default     = 300
  
  validation {
    condition     = var.scale_in_cooldown > 0
    error_message = "The scale_in_cooldown must be greater than 0."
  }
}

# Health Check Configuration
variable "health_check_grace_period" {
  description = "Time in seconds after instance comes into service before checking health"
  type        = number
  default     = 300
  
  validation {
    condition     = var.health_check_grace_period > 0
    error_message = "The health_check_grace_period must be greater than 0."
  }
}

# Tagging
variable "tags" {
  description = "Tags to apply to all resources created by this module"
  type        = map(string)
  default     = {}
}