# AWS Provider data sources to get current account and region information
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Local variables for resource naming and tagging
locals {
  resource_prefix = "${var.project_name}-${var.environment}"
  common_tags     = merge(var.tags, {
    Environment = var.environment
    ManagedBy   = "terraform"
  })
}

#------------------------------------------------------
# CloudWatch Log Groups
#------------------------------------------------------
resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/aws/interaction-management/${var.environment}/frontend"
  retention_in_days = var.monitoring.log_retention_days
  kms_key_id        = var.kms_key_id
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/aws/interaction-management/${var.environment}/backend"
  retention_in_days = var.monitoring.log_retention_days
  kms_key_id        = var.kms_key_id
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "error" {
  name              = "/aws/interaction-management/${var.environment}/error"
  retention_in_days = var.monitoring.log_retention_days
  kms_key_id        = var.kms_key_id
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "audit" {
  name              = "/aws/interaction-management/${var.environment}/audit"
  retention_in_days = var.monitoring.log_retention_days
  kms_key_id        = var.kms_key_id
  tags              = local.common_tags
}

#------------------------------------------------------
# SNS Topics for Notifications
#------------------------------------------------------
resource "aws_sns_topic" "alarm_notification_critical" {
  name             = "${local.resource_prefix}-alarms-critical"
  display_name     = "Interaction Management Critical Alerts"
  kms_master_key_id = var.kms_key_id
  tags             = local.common_tags
}

resource "aws_sns_topic" "alarm_notification_warning" {
  name             = "${local.resource_prefix}-alarms-warning"
  display_name     = "Interaction Management Warning Alerts"
  kms_master_key_id = var.kms_key_id
  tags             = local.common_tags
}

resource "aws_sns_topic" "alarm_notification_info" {
  name             = "${local.resource_prefix}-alarms-info"
  display_name     = "Interaction Management Info Alerts"
  kms_master_key_id = var.kms_key_id
  tags             = local.common_tags
}

#------------------------------------------------------
# SNS Topic Subscriptions
#------------------------------------------------------
resource "aws_sns_topic_subscription" "email_critical" {
  for_each  = toset(var.sns_topic_subscriptions.email)
  topic_arn = aws_sns_topic.alarm_notification_critical.arn
  protocol  = "email"
  endpoint  = each.value
}

resource "aws_sns_topic_subscription" "email_warning" {
  for_each  = toset(var.sns_topic_subscriptions.email)
  topic_arn = aws_sns_topic.alarm_notification_warning.arn
  protocol  = "email"
  endpoint  = each.value
}

resource "aws_sns_topic_subscription" "sms_critical" {
  for_each  = toset(var.sns_topic_subscriptions.sms)
  topic_arn = aws_sns_topic.alarm_notification_critical.arn
  protocol  = "sms"
  endpoint  = each.value
}

#------------------------------------------------------
# CloudWatch Alarms - CPU Utilization
#------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "cpu_utilization_high" {
  alarm_name          = "${local.resource_prefix}-cpu-utilization-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = var.monitoring.alert_thresholds.cpu_utilization_critical
  alarm_description   = "Critical CPU utilization threshold exceeded"
  alarm_actions       = [aws_sns_topic.alarm_notification_critical.arn]
  ok_actions          = [aws_sns_topic.alarm_notification_info.arn]
  
  dimensions = {
    Environment = var.environment
    Component   = "Application"
  }
  
  tags = local.common_tags
}

#------------------------------------------------------
# CloudWatch Alarms - Memory Usage
#------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "memory_usage_high" {
  alarm_name          = "${local.resource_prefix}-memory-usage-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "MemoryUtilization"
  namespace           = "CWAgent"
  period              = 300
  statistic           = "Average"
  threshold           = var.monitoring.alert_thresholds.memory_usage_critical
  alarm_description   = "Critical memory utilization threshold exceeded"
  alarm_actions       = [aws_sns_topic.alarm_notification_critical.arn]
  ok_actions          = [aws_sns_topic.alarm_notification_info.arn]
  
  dimensions = {
    Environment = var.environment
    Component   = "Application"
  }
  
  tags = local.common_tags
}

#------------------------------------------------------
# CloudWatch Alarms - API Performance
#------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "api_response_time" {
  alarm_name          = "${local.resource_prefix}-api-response-time-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApiResponseTime"
  namespace           = "InteractionManagement"
  period              = 60
  statistic           = "p95"
  threshold           = var.monitoring.alert_thresholds.api_response_time_critical
  alarm_description   = "API response time exceeding critical threshold"
  alarm_actions       = [aws_sns_topic.alarm_notification_critical.arn]
  ok_actions          = [aws_sns_topic.alarm_notification_info.arn]
  
  dimensions = {
    Environment = var.environment
    Component   = "Backend"
  }
  
  tags = local.common_tags
}

#------------------------------------------------------
# CloudWatch Alarms - Error Rate
#------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "error_rate_high" {
  alarm_name          = "${local.resource_prefix}-error-rate-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApiErrorRate"
  namespace           = "InteractionManagement"
  period              = 300
  statistic           = "Average"
  threshold           = var.monitoring.alert_thresholds.error_rate_critical
  alarm_description   = "API error rate exceeding critical threshold"
  alarm_actions       = [aws_sns_topic.alarm_notification_critical.arn]
  ok_actions          = [aws_sns_topic.alarm_notification_info.arn]
  
  dimensions = {
    Environment = var.environment
    Component   = "Backend"
  }
  
  tags = local.common_tags
}

#------------------------------------------------------
# CloudWatch Alarms - Database Performance
#------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "database_query_time" {
  alarm_name          = "${local.resource_prefix}-db-query-time-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "QueryExecutionTime"
  namespace           = "InteractionManagement"
  period              = 300
  statistic           = "Average"
  threshold           = var.monitoring.alert_thresholds.database_query_time_critical
  alarm_description   = "Database query execution time exceeding critical threshold"
  alarm_actions       = [aws_sns_topic.alarm_notification_critical.arn]
  ok_actions          = [aws_sns_topic.alarm_notification_info.arn]
  
  dimensions = {
    Environment = var.environment
    Component   = "Database"
  }
  
  tags = local.common_tags
}

#------------------------------------------------------
# CloudWatch Alarms - Cache Performance
#------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "cache_hit_ratio_low" {
  alarm_name          = "${local.resource_prefix}-cache-hit-ratio-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CacheHitRate"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = var.monitoring.alert_thresholds.cache_hit_ratio_critical
  alarm_description   = "Cache hit ratio below critical threshold"
  alarm_actions       = [aws_sns_topic.alarm_notification_warning.arn]
  ok_actions          = [aws_sns_topic.alarm_notification_info.arn]
  
  dimensions = {
    Environment = var.environment
    Service     = "ElastiCache"
  }
  
  tags = local.common_tags
}

#------------------------------------------------------
# CloudWatch Log Metric Filters
#------------------------------------------------------
resource "aws_cloudwatch_log_metric_filter" "error_logs" {
  name            = "${local.resource_prefix}-error-logs"
  pattern         = "ERROR"
  log_group_name  = aws_cloudwatch_log_group.error.name

  metric_transformation {
    name          = "ErrorCount"
    namespace     = "InteractionManagement"
    value         = "1"
    dimensions = {
      Environment = var.environment
    }
  }
}

resource "aws_cloudwatch_log_metric_filter" "api_response_time" {
  name            = "${local.resource_prefix}-api-response-time"
  pattern         = "[timestamp, request_id, method, path, status_code, response_time]"
  log_group_name  = aws_cloudwatch_log_group.backend.name

  metric_transformation {
    name          = "ApiResponseTime"
    namespace     = "InteractionManagement"
    value         = "$response_time"
    dimensions = {
      Environment = var.environment
      Component   = "Backend"
    }
  }
}

resource "aws_cloudwatch_log_metric_filter" "authentication_failures" {
  name            = "${local.resource_prefix}-auth-failures"
  pattern         = "?Authentication failed ?Failed login ?Invalid credentials"
  log_group_name  = aws_cloudwatch_log_group.backend.name

  metric_transformation {
    name          = "AuthenticationFailures"
    namespace     = "InteractionManagement"
    value         = "1"
    dimensions = {
      Environment = var.environment
    }
  }
}

#------------------------------------------------------
# CloudWatch Dashboard
#------------------------------------------------------
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${local.resource_prefix}-dashboard"
  
  dashboard_body = templatefile(
    fileexists("${path.module}/templates/dashboard.json") ? 
      "${path.module}/templates/dashboard.json" : 
      "${path.module}/../../../monitoring/cloudwatch-dashboard.json",
    {
      resource_prefix              = local.resource_prefix
      AWS_REGION                   = data.aws_region.current.name
      ENVIRONMENT                  = var.environment
      FRONTEND_ASG_NAME            = length(var.frontend_resources) > 0 ? var.frontend_resources[0] : ""
      BACKEND_ASG_NAME             = length(var.backend_resources) > 0 ? var.backend_resources[0] : ""
      CACHE_CLUSTER_ID             = length(var.cache_resources) > 0 ? var.cache_resources[0] : ""
      DB_INSTANCE_ID               = "placeholder" # Replace with actual DB instance ID when available
      ALB_NAME                     = "placeholder" # Replace with actual ALB name when available
      HEALTH_CHECK_ID              = "placeholder" # Replace with actual Health Check ID when available
      DB_CONNECTION_THRESHOLD_WARNING = "70" # Example warning threshold
      DB_CONNECTION_THRESHOLD_CRITICAL = "90" # Example critical threshold
    }
  )
}