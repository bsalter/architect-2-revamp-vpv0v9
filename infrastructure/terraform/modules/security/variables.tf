# General variables
variable "environment" {
  description = "Environment name used for resource naming and tagging (e.g., dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "interaction-mgmt"
}

variable "aws_region" {
  description = "AWS region where resources will be deployed"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources created by this module"
  type        = map(string)
  default     = {}
}

# KMS key configuration
variable "kms_key_deletion_window_in_days" {
  description = "Duration in days after which KMS keys are deleted when scheduled for deletion"
  type        = number
  default     = 30
}

variable "enable_key_rotation" {
  description = "Whether to enable automatic KMS key rotation"
  type        = bool
  default     = true
}

variable "create_database_encryption_key" {
  description = "Whether to create a KMS key for database encryption"
  type        = bool
  default     = true
}

variable "create_cloudwatch_encryption_key" {
  description = "Whether to create a KMS key for CloudWatch logs encryption"
  type        = bool
  default     = true
}

variable "create_s3_encryption_key" {
  description = "Whether to create a KMS key for S3 bucket encryption"
  type        = bool
  default     = true
}

# Network configuration
variable "vpc_id" {
  description = "VPC ID where security groups will be created"
  type        = string
}

# IAM roles configuration
variable "create_ec2_instance_profile" {
  description = "Whether to create IAM instance profile for EC2 instances"
  type        = bool
  default     = true
}

variable "create_ecs_task_execution_role" {
  description = "Whether to create IAM role for ECS task execution"
  type        = bool
  default     = true
}

variable "create_ecs_task_role" {
  description = "Whether to create IAM role for ECS tasks"
  type        = bool
  default     = true
}

variable "create_cloudwatch_logs_role" {
  description = "Whether to create IAM role for CloudWatch logs"
  type        = bool
  default     = true
}

# Security services configuration
variable "cloudtrail_enabled" {
  description = "Whether to enable AWS CloudTrail for comprehensive API activity logging"
  type        = bool
  default     = false
}

variable "waf_enabled" {
  description = "Whether to enable AWS WAF for web application firewall protection"
  type        = bool
  default     = false
}

variable "waf_rules" {
  description = "List of WAF rules to apply if WAF is enabled"
  type = list(object({
    name     = string
    priority = number
    action   = string
    statement = any
  }))
  default = []
}

# Parameter Store configuration
variable "ssm_parameter_prefix" {
  description = "Prefix for SSM parameters created by this module"
  type        = string
  default     = null

  validation {
    condition     = var.ssm_parameter_prefix == null ? true : length(var.ssm_parameter_prefix) > 0
    error_message = "SSM parameter prefix must not be empty string if provided."
  }
}

locals {
  ssm_parameter_prefix = var.ssm_parameter_prefix == null ? "/${var.project_name}/${var.environment}/" : var.ssm_parameter_prefix
}

variable "ssm_secure_parameters" {
  description = "Map of secure parameters to create in SSM Parameter Store"
  type = map(object({
    description = string
    type        = string
    value       = string
    secure      = bool
  }))
  default = {}

  validation {
    condition = alltrue([
      for k, v in var.ssm_secure_parameters : contains(["String", "StringList", "SecureString"], v.type)
    ])
    error_message = "The type for SSM parameters must be one of 'String', 'StringList', or 'SecureString'."
  }
}