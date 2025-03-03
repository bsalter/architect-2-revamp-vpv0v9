terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Get current AWS account ID and region for use in policies
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Local variables for consistent naming and tagging
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
    }
  )
}

#######################
# KMS Encryption Keys #
#######################

# Database encryption KMS key
resource "aws_kms_key" "database_encryption" {
  count                   = var.create_database_encryption_key ? 1 : 0
  description             = "KMS key for ${local.name_prefix} database encryption"
  deletion_window_in_days = var.kms_key_deletion_window_in_days
  enable_key_rotation     = var.enable_key_rotation
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow RDS Service"
        Effect = "Allow"
        Principal = {
          Service = "rds.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Sid    = "Allow Application Access"
        Effect = "Allow"
        Principal = {
          AWS = var.create_ecs_task_role ? [aws_iam_role.ecs_task_role[0].arn] : ["*"]
        }
        Action   = ["kms:Decrypt"]
        Resource = "*"
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_kms_alias" "database_encryption" {
  count         = var.create_database_encryption_key ? 1 : 0
  name          = "alias/${local.name_prefix}-db-encryption"
  target_key_id = aws_kms_key.database_encryption[0].key_id
}

# CloudWatch logs encryption KMS key
resource "aws_kms_key" "cloudwatch_encryption" {
  count                   = var.create_cloudwatch_encryption_key ? 1 : 0
  description             = "KMS key for ${local.name_prefix} CloudWatch logs encryption"
  deletion_window_in_days = var.kms_key_deletion_window_in_days
  enable_key_rotation     = var.enable_key_rotation
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch Service"
        Effect = "Allow"
        Principal = {
          Service = "logs.${data.aws_region.current.name}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Sid    = "Allow Application Access"
        Effect = "Allow"
        Principal = {
          AWS = var.create_ecs_task_role ? [aws_iam_role.ecs_task_role[0].arn] : ["*"]
        }
        Action   = ["kms:Decrypt"]
        Resource = "*"
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_kms_alias" "cloudwatch_encryption" {
  count         = var.create_cloudwatch_encryption_key ? 1 : 0
  name          = "alias/${local.name_prefix}-cloudwatch-encryption"
  target_key_id = aws_kms_key.cloudwatch_encryption[0].key_id
}

# S3 encryption KMS key
resource "aws_kms_key" "s3_encryption" {
  count                   = var.create_s3_encryption_key ? 1 : 0
  description             = "KMS key for ${local.name_prefix} S3 bucket encryption"
  deletion_window_in_days = var.kms_key_deletion_window_in_days
  enable_key_rotation     = var.enable_key_rotation
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow S3 Service"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Sid    = "Allow Application Access"
        Effect = "Allow"
        Principal = {
          AWS = var.create_ecs_task_role ? [aws_iam_role.ecs_task_role[0].arn] : ["*"]
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey*"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_kms_alias" "s3_encryption" {
  count         = var.create_s3_encryption_key ? 1 : 0
  name          = "alias/${local.name_prefix}-s3-encryption"
  target_key_id = aws_kms_key.s3_encryption[0].key_id
}

#############
# IAM Roles #
#############

# EC2 instance role and profile
resource "aws_iam_role" "ec2_instance_role" {
  count = var.create_ec2_instance_profile ? 1 : 0
  name  = "${local.name_prefix}-ec2-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_iam_role_policy" "ec2_instance_policy" {
  count  = var.create_ec2_instance_profile ? 1 : 0
  name   = "${aws_iam_role.ec2_instance_role[0].name}-policy"
  role   = aws_iam_role.ec2_instance_role[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "cloudwatch:GetMetricData",
          "cloudwatch:GetMetricStatistics"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:*:*:parameter/${var.project_name}/${var.environment}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ]
        Resource = var.create_database_encryption_key ? aws_kms_key.database_encryption[0].arn : "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.project_name}-${var.environment}-static",
          "arn:aws:s3:::${var.project_name}-${var.environment}-static/*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_instance_profile" {
  count = var.create_ec2_instance_profile ? 1 : 0
  name  = "${local.name_prefix}-ec2-profile"
  role  = aws_iam_role.ec2_instance_role[0].name
}

# ECS task execution role
resource "aws_iam_role" "ecs_task_execution_role" {
  count = var.create_ecs_task_execution_role ? 1 : 0
  name  = "${local.name_prefix}-ecs-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_iam_role_policy" "ecs_task_execution_policy" {
  count  = var.create_ecs_task_execution_role ? 1 : 0
  name   = "${aws_iam_role.ecs_task_execution_role[0].name}-policy"
  role   = aws_iam_role.ecs_task_execution_role[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "ssm:GetParameter",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:*:*:parameter/${var.project_name}/${var.environment}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ]
        Resource = var.create_database_encryption_key ? aws_kms_key.database_encryption[0].arn : "*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:*:*:secret:${var.project_name}/${var.environment}/*"
      }
    ]
  })
}

# ECS task role
resource "aws_iam_role" "ecs_task_role" {
  count = var.create_ecs_task_role ? 1 : 0
  name  = "${local.name_prefix}-ecs-task-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_iam_role_policy" "ecs_task_policy" {
  count  = var.create_ecs_task_role ? 1 : 0
  name   = "${aws_iam_role.ecs_task_role[0].name}-policy"
  role   = aws_iam_role.ecs_task_role[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.project_name}-${var.environment}-app",
          "arn:aws:s3:::${var.project_name}-${var.environment}-app/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = "arn:aws:sqs:*:*:${var.project_name}-${var.environment}-*"
      },
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "elasticache:DescribeCacheClusters",
          "elasticache:DescribeReplicationGroups"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey"
        ]
        Resource = var.create_s3_encryption_key ? aws_kms_key.s3_encryption[0].arn : "*"
      }
    ]
  })
}

# CloudWatch logs role
resource "aws_iam_role" "cloudwatch_logs_role" {
  count = var.create_cloudwatch_logs_role ? 1 : 0
  name  = "${local.name_prefix}-cloudwatch-logs-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "logs.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_iam_role_policy" "cloudwatch_logs_policy" {
  count  = var.create_cloudwatch_logs_role ? 1 : 0
  name   = "${aws_iam_role.cloudwatch_logs_role[0].name}-policy"
  role   = aws_iam_role.cloudwatch_logs_role[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:PutRetentionPolicy",
          "logs:PutMetricFilter",
          "logs:GetLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = var.create_cloudwatch_encryption_key ? aws_kms_key.cloudwatch_encryption[0].arn : "*"
      }
    ]
  })
}

####################
# Security Groups #
####################

resource "aws_security_group" "admin_access" {
  name        = "${local.name_prefix}-admin-access"
  description = "Security group for administrative access to resources"
  vpc_id      = var.vpc_id
  
  # SSH access from specified CIDR blocks (should be restricted in production)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"] # Example; should be more restricted
    description = "SSH access for administration"
  }
  
  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-admin-access"
    }
  )
}

# Application security group
resource "aws_security_group" "app_security_group" {
  name        = "${local.name_prefix}-app-sg"
  description = "Security group for application tier"
  vpc_id      = var.vpc_id
  
  # HTTP/HTTPS access
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP access"
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS access"
  }
  
  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-app-sg"
    }
  )
}

# Database security group
resource "aws_security_group" "db_security_group" {
  name        = "${local.name_prefix}-db-sg"
  description = "Security group for database tier"
  vpc_id      = var.vpc_id
  
  # Allow access from application security group
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_security_group.id]
    description     = "PostgreSQL access from application tier"
  }
  
  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-db-sg"
    }
  )
}

##################
# AWS CloudTrail #
##################

resource "aws_cloudtrail" "trail" {
  count                         = var.cloudtrail_enabled ? 1 : 0
  name                          = "${local.name_prefix}-trail"
  s3_bucket_name                = "${local.name_prefix}-cloudtrail-logs"
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  
  # Use KMS key for log encryption if available
  kms_key_id = var.create_cloudwatch_encryption_key ? aws_kms_key.cloudwatch_encryption[0].arn : null
  
  tags = local.common_tags
}

##########
# AWS WAF #
##########

resource "aws_wafv2_web_acl" "main" {
  count       = var.waf_enabled ? 1 : 0
  name        = "${local.name_prefix}-web-acl"
  description = "WAF Web ACL for ${local.name_prefix}"
  scope       = "REGIONAL"
  
  default_action {
    allow {}
  }
  
  dynamic "rule" {
    for_each = var.waf_rules
    content {
      name     = rule.value.name
      priority = rule.value.priority
      
      action {
        dynamic "block" {
          for_each = rule.value.action == "block" ? [1] : []
          content {}
        }
        
        dynamic "allow" {
          for_each = rule.value.action == "allow" ? [1] : []
          content {}
        }
        
        dynamic "count" {
          for_each = rule.value.action == "count" ? [1] : []
          content {}
        }
      }
      
      statement {
        dynamic "rate_based_statement" {
          for_each = try(rule.value.statement.rate_based_statement, null) != null ? [rule.value.statement.rate_based_statement] : []
          content {
            limit              = rate_based_statement.value.limit
            aggregate_key_type = rate_based_statement.value.aggregate_key_type
          }
        }
        
        dynamic "xss_match_statement" {
          for_each = try(rule.value.statement.xss_match_statement, null) != null ? [rule.value.statement.xss_match_statement] : []
          content {
            dynamic "field_to_match" {
              for_each = [xss_match_statement.value.field_to_match]
              content {
                dynamic "body" {
                  for_each = try(field_to_match.value.body, null) != null ? [1] : []
                  content {}
                }
                dynamic "uri_path" {
                  for_each = try(field_to_match.value.uri_path, null) != null ? [1] : []
                  content {}
                }
                dynamic "query_string" {
                  for_each = try(field_to_match.value.query_string, null) != null ? [1] : []
                  content {}
                }
                dynamic "single_header" {
                  for_each = try(field_to_match.value.single_header, null) != null ? [field_to_match.value.single_header] : []
                  content {
                    name = single_header.value.name
                  }
                }
              }
            }
            text_transformation {
              priority = xss_match_statement.value.text_transformation.priority
              type     = xss_match_statement.value.text_transformation.type
            }
          }
        }
        
        dynamic "sqli_match_statement" {
          for_each = try(rule.value.statement.sqli_match_statement, null) != null ? [rule.value.statement.sqli_match_statement] : []
          content {
            dynamic "field_to_match" {
              for_each = [sqli_match_statement.value.field_to_match]
              content {
                dynamic "body" {
                  for_each = try(field_to_match.value.body, null) != null ? [1] : []
                  content {}
                }
                dynamic "uri_path" {
                  for_each = try(field_to_match.value.uri_path, null) != null ? [1] : []
                  content {}
                }
                dynamic "query_string" {
                  for_each = try(field_to_match.value.query_string, null) != null ? [1] : []
                  content {}
                }
                dynamic "single_header" {
                  for_each = try(field_to_match.value.single_header, null) != null ? [field_to_match.value.single_header] : []
                  content {
                    name = single_header.value.name
                  }
                }
              }
            }
            text_transformation {
              priority = sqli_match_statement.value.text_transformation.priority
              type     = sqli_match_statement.value.text_transformation.type
            }
          }
        }
      }
    }
  }
  
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-waf-metrics"
    sampled_requests_enabled   = true
  }
  
  tags = local.common_tags
}

#####################
# SSM Parameters Store #
#####################

resource "aws_ssm_parameter" "secure_parameters" {
  for_each = var.ssm_secure_parameters
  
  name        = "${local.ssm_parameter_prefix}${each.key}"
  description = each.value.description
  type        = each.value.type
  value       = each.value.value
  
  # Use KMS key for encryption if type is SecureString and KMS key is available
  key_id      = each.value.type == "SecureString" && var.create_database_encryption_key ? aws_kms_key.database_encryption[0].arn : null
  
  tags = local.common_tags
}

###########
# Outputs #
###########

output "kms_key_arns" {
  description = "Map of KMS key ARNs for different encryption purposes"
  value = {
    database   = var.create_database_encryption_key ? aws_kms_key.database_encryption[0].arn : null
    cloudwatch = var.create_cloudwatch_encryption_key ? aws_kms_key.cloudwatch_encryption[0].arn : null
    s3         = var.create_s3_encryption_key ? aws_kms_key.s3_encryption[0].arn : null
  }
}

output "kms_key_id" {
  description = "Primary KMS key ID for general encryption needs"
  value       = var.create_database_encryption_key ? aws_kms_key.database_encryption[0].id : null
}

output "ec2_instance_profile_name" {
  description = "Name of the IAM instance profile for EC2 instances"
  value       = var.create_ec2_instance_profile ? aws_iam_instance_profile.ec2_instance_profile[0].name : null
}

output "ec2_instance_profile_arn" {
  description = "ARN of the IAM instance profile for EC2 instances"
  value       = var.create_ec2_instance_profile ? aws_iam_instance_profile.ec2_instance_profile[0].arn : null
}

output "iam_role_ecs_task_execution_arn" {
  description = "ARN of the IAM role for ECS task execution"
  value       = var.create_ecs_task_execution_role ? aws_iam_role.ecs_task_execution_role[0].arn : null
}

output "iam_role_ecs_task_arn" {
  description = "ARN of the IAM role for ECS tasks"
  value       = var.create_ecs_task_role ? aws_iam_role.ecs_task_role[0].arn : null
}

output "cloudwatch_logs_role_arn" {
  description = "ARN of the IAM role for CloudWatch logs"
  value       = var.create_cloudwatch_logs_role ? aws_iam_role.cloudwatch_logs_role[0].arn : null
}

output "ssm_parameter_arns" {
  description = "List of ARNs for created SSM parameters"
  value       = [for param in aws_ssm_parameter.secure_parameters : param.arn]
}

output "security_group_ids" {
  description = "Map of security group IDs created by the module"
  value = {
    admin = aws_security_group.admin_access.id
    app   = aws_security_group.app_security_group.id
    db    = aws_security_group.db_security_group.id
  }
}

output "cloudtrail_id" {
  description = "ID of the CloudTrail trail if enabled"
  value       = var.cloudtrail_enabled ? aws_cloudtrail.trail[0].id : null
}

output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL if enabled"
  value       = var.waf_enabled ? aws_wafv2_web_acl.main[0].id : null
}