variable "environment" {
  description = "Environment name for resource naming and configuration (dev, staging, prod)"
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
    condition     = can(regex("^[a-zA-Z0-9-_]+$", var.project_name))
    error_message = "Project name must contain only alphanumeric characters, hyphens, and underscores."
  }
}

variable "monitoring" {
  description = "Monitoring configuration object containing alert thresholds and settings"
  type = object({
    enable_detailed_monitoring = bool
    create_dashboard           = bool
    log_retention_days         = number
    alert_thresholds = object({
      # CPU thresholds (percentage)
      cpu_utilization_warning   = number
      cpu_utilization_critical  = number
      
      # Memory thresholds (percentage)
      memory_usage_warning      = number
      memory_usage_critical     = number
      
      # API performance thresholds (milliseconds)
      api_response_time_warning  = number
      api_response_time_critical = number
      
      # Error rate thresholds (percentage)
      error_rate_warning        = number
      error_rate_critical       = number
      
      # Database thresholds (milliseconds)
      database_query_time_warning  = number
      database_query_time_critical = number
      
      # Cache thresholds (percentage)
      cache_hit_ratio_warning   = number
      cache_hit_ratio_critical  = number
    })
  })
  
  default = {
    enable_detailed_monitoring = true
    create_dashboard           = true
    log_retention_days         = 30
    alert_thresholds = {
      # Default values based on SLA matrix
      cpu_utilization_warning   = 70
      cpu_utilization_critical  = 85
      
      memory_usage_warning      = 70
      memory_usage_critical     = 85
      
      api_response_time_warning  = 500  # milliseconds
      api_response_time_critical = 2000 # milliseconds
      
      error_rate_warning        = 1  # percentage
      error_rate_critical       = 5  # percentage
      
      database_query_time_warning  = 300  # milliseconds
      database_query_time_critical = 1000 # milliseconds
      
      cache_hit_ratio_warning   = 80 # percentage (below this is warning)
      cache_hit_ratio_critical  = 60 # percentage (below this is critical)
    }
  }
  
  validation {
    condition = (
      var.monitoring.alert_thresholds.cpu_utilization_warning < var.monitoring.alert_thresholds.cpu_utilization_critical &&
      var.monitoring.alert_thresholds.memory_usage_warning < var.monitoring.alert_thresholds.memory_usage_critical &&
      var.monitoring.alert_thresholds.api_response_time_warning < var.monitoring.alert_thresholds.api_response_time_critical &&
      var.monitoring.alert_thresholds.error_rate_warning < var.monitoring.alert_thresholds.error_rate_critical &&
      var.monitoring.alert_thresholds.database_query_time_warning < var.monitoring.alert_thresholds.database_query_time_critical &&
      var.monitoring.alert_thresholds.cache_hit_ratio_warning > var.monitoring.alert_thresholds.cache_hit_ratio_critical
    )
    error_message = "Warning thresholds must be less severe than critical thresholds (except for cache_hit_ratio where warning should be greater than critical)."
  }
}

variable "tags" {
  description = "Resource tags to apply to all monitoring resources"
  type        = map(string)
  default     = {}
}

variable "frontend_resources" {
  description = "List of frontend resources to monitor (EC2 instances, ASGs or ECS containers)"
  type        = list(string)
  default     = []
}

variable "backend_resources" {
  description = "List of backend resources to monitor (EC2 instances, ASGs or ECS containers)"
  type        = list(string)
  default     = []
}

variable "cache_resources" {
  description = "List of cache resources to monitor (ElastiCache clusters)"
  type        = list(string)
  default     = []
}

variable "kms_key_id" {
  description = "KMS key ID for encrypting log groups and SNS topics"
  type        = string
  default     = null
}

variable "sns_topic_subscriptions" {
  description = "Map of email addresses and phone numbers for SNS notifications"
  type = object({
    email = list(string)
    sms   = list(string)
  })
  
  default = {
    email = []
    sms   = []
  }
  
  validation {
    condition = alltrue([
      for email in var.sns_topic_subscriptions.email : 
      can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", email))
    ])
    error_message = "All email addresses must be in valid format (example@domain.com)."
  }
}

variable "dashboard_widgets" {
  description = "Additional dashboard widgets to include in the CloudWatch dashboard"
  type        = list(any)
  default     = []
}