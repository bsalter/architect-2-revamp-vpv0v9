# Security groups outputs
output "web_security_group_id" {
  description = "ID of the security group for web tier resources"
  value       = aws_security_group.web.id
}

output "app_security_group_id" {
  description = "ID of the security group for application tier resources"
  value       = aws_security_group.app.id
}

output "data_security_group_id" {
  description = "ID of the security group for database tier resources"
  value       = aws_security_group.data.id
}

output "redis_security_group_id" {
  description = "ID of the security group for Redis cache resources"
  value       = aws_security_group.redis.id
}

# IAM role outputs
output "ecs_task_execution_role_arn" {
  description = "ARN of the IAM role for ECS task execution"
  value       = aws_iam_role.ecs_task_execution_role.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the IAM role for ECS tasks to access AWS services"
  value       = aws_iam_role.ecs_task_role.arn
}

# Encryption key outputs
output "database_encryption_key_arn" {
  description = "ARN of the KMS key for database encryption"
  value       = aws_kms_key.database_encryption.arn
}

output "secrets_encryption_key_arn" {
  description = "ARN of the KMS key for secrets encryption"
  value       = aws_kms_key.secrets_encryption.arn
}

# WAF outputs
output "waf_web_acl_arn" {
  description = "ARN of the WAF WebACL for application protection"
  value       = aws_wafv2_web_acl.main.arn
}

# Logging and monitoring outputs
output "cloudtrail_log_group_arn" {
  description = "ARN of the CloudWatch Log Group for CloudTrail"
  value       = aws_cloudwatch_log_group.cloudtrail.arn
}

output "guardduty_detector_id" {
  description = "ID of the GuardDuty detector for threat detection"
  value       = aws_guardduty_detector.main.id
}

# Aggregated maps for more convenient referencing from other modules
output "security_groups" {
  description = "Map of all security group IDs by name"
  value = {
    web   = aws_security_group.web.id
    app   = aws_security_group.app.id
    data  = aws_security_group.data.id
    redis = aws_security_group.redis.id
  }
}

output "iam_roles" {
  description = "Map of all IAM role ARNs by name"
  value = {
    ecs_task_execution = aws_iam_role.ecs_task_execution_role.arn
    ecs_task           = aws_iam_role.ecs_task_role.arn
  }
}

output "kms_keys" {
  description = "Map of all KMS key ARNs by name"
  value = {
    database = aws_kms_key.database_encryption.arn
    secrets  = aws_kms_key.secrets_encryption.arn
  }
}