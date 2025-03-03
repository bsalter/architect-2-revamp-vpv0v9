# Output variables for the monitoring module
# Provides access to monitoring resources and configurations

output "dashboard_url" {
  description = "URL to access the CloudWatch dashboard for monitoring the system"
  value       = "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "log_groups" {
  description = "Map of log group names for different components"
  value = {
    frontend = aws_cloudwatch_log_group.frontend.name
    backend  = aws_cloudwatch_log_group.backend.name
    error    = aws_cloudwatch_log_group.error.name
    audit    = aws_cloudwatch_log_group.audit.name
  }
}

output "alarm_topic_arns" {
  description = "ARNs of SNS topics used for different alert severities"
  value = {
    critical = aws_sns_topic.alarm_notification_critical.arn
    warning  = aws_sns_topic.alarm_notification_warning.arn
    info     = aws_sns_topic.alarm_notification_info.arn
  }
}

output "alarm_names" {
  description = "Names of CloudWatch alarms created by the module"
  value = [
    aws_cloudwatch_metric_alarm.cpu_utilization_high.alarm_name,
    aws_cloudwatch_metric_alarm.memory_usage_high.alarm_name,
    aws_cloudwatch_metric_alarm.api_response_time.alarm_name,
    aws_cloudwatch_metric_alarm.error_rate_high.alarm_name,
    aws_cloudwatch_metric_alarm.database_query_time.alarm_name,
    aws_cloudwatch_metric_alarm.cache_hit_ratio_low.alarm_name
  ]
}

output "log_metric_filters" {
  description = "Log metric filters created for monitoring key metrics"
  value = {
    error_logs              = aws_cloudwatch_log_metric_filter.error_logs.name
    api_response_time       = aws_cloudwatch_log_metric_filter.api_response_time.name
    authentication_failures = aws_cloudwatch_log_metric_filter.authentication_failures.name
  }
}

output "monitoring_namespace" {
  description = "CloudWatch namespace used for custom metrics"
  value       = "InteractionManagement"
}