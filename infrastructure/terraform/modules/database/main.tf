# infrastructure/terraform/modules/database/main.tf

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

locals {
  engine_version       = "15.3"              # PostgreSQL version specified in tech stack
  instance_class       = "db.t3.large"       # As specified in cloud services requirements
  allocated_storage    = 100                 # 100GB as specified in requirements
  database_name        = var.database_name != "" ? var.database_name : "interactions"
  username             = var.database_username != "" ? var.database_username : "interactionapp"
  redis_engine_version = "7.0.12"            # Redis version specified in tech stack
  redis_node_type      = "cache.t3.medium"   # As specified in cloud services requirements
  
  # Determine if this is a production environment - used for enhanced security and availability settings
  is_production = var.environment == "production"
  
  # Common tags for all resources
  common_tags = merge({
    Name        = "${var.name_prefix}-database"
    Environment = var.environment
    Terraform   = "true"
    Module      = "database"
  }, var.tags)
}

# Create a random password for the database
resource "random_password" "db_password" {
  length           = 16
  special          = true
  # Use only special characters that are valid in connection strings
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Store the database credentials in AWS Secrets Manager
resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${var.name_prefix}-db-credentials-${var.environment}"
  description = "Database credentials for the ${var.environment} environment"
  tags        = local.common_tags
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = local.username
    password = random_password.db_password.result
    engine   = "postgres"
    host     = aws_db_instance.postgres.address
    port     = aws_db_instance.postgres.port
    dbname   = local.database_name
  })
  # Ensures we only create this after the DB instance is ready
  depends_on = [aws_db_instance.postgres]
}

# Security group for database access
resource "aws_security_group" "database" {
  name        = "${var.name_prefix}-database-sg-${var.environment}"
  description = "Security group for ${var.environment} database resources"
  vpc_id      = var.vpc_id

  # PostgreSQL
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.app_security_group_ids
    description     = "PostgreSQL access from application servers"
  }

  # Redis
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = var.app_security_group_ids
    description     = "Redis access from application servers"
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge({
    Name = "${var.name_prefix}-database-sg-${var.environment}"
  }, local.common_tags)
}

# Subnet group for RDS
resource "aws_db_subnet_group" "postgres" {
  name       = "${var.name_prefix}-db-subnet-group-${var.environment}"
  subnet_ids = var.subnet_ids
  
  tags = merge({
    Name = "${var.name_prefix}-db-subnet-group-${var.environment}"
  }, local.common_tags)
}

# Parameter group for PostgreSQL
resource "aws_db_parameter_group" "postgres" {
  name        = "${var.name_prefix}-pg-params-${var.environment}"
  family      = "postgres15"
  description = "Parameter group for PostgreSQL ${local.engine_version} in ${var.environment} environment"

  # Performance optimization parameters based on instance size
  parameter {
    name  = "shared_buffers"
    value = "2GB"  # Recommended to use 25% of instance memory
    apply_method = "pending-reboot"
  }

  parameter {
    name  = "max_connections"
    value = "200"  # Appropriate for the application needs
    apply_method = "pending-reboot"
  }

  parameter {
    name  = "work_mem"
    value = "16MB"  # Reasonable value for mixed workloads
    apply_method = "pending-reboot"
  }

  # Enable full-text search capabilities for the finder
  parameter {
    name  = "default_text_search_config"
    value = "pg_catalog.english"
    apply_method = "pending-reboot"
  }

  tags = merge({
    Name = "${var.name_prefix}-pg-params-${var.environment}"
  }, local.common_tags)
}

# PostgreSQL RDS instance
resource "aws_db_instance" "postgres" {
  identifier                  = "${var.name_prefix}-postgres-${var.environment}"
  allocated_storage           = local.allocated_storage
  storage_type                = "gp3"
  iops                        = 3000  # As specified in requirements
  engine                      = "postgres"
  engine_version              = local.engine_version
  instance_class              = local.instance_class
  db_name                     = local.database_name
  username                    = local.username
  password                    = random_password.db_password.result
  parameter_group_name        = aws_db_parameter_group.postgres.name
  db_subnet_group_name        = aws_db_subnet_group.postgres.name
  vpc_security_group_ids      = [aws_security_group.database.id]
  
  # High availability and backup settings
  multi_az                    = local.is_production ? true : var.multi_az
  backup_retention_period     = local.is_production ? 30 : var.backup_retention_period
  backup_window               = "03:00-05:00"  # UTC time
  maintenance_window          = "sun:05:00-sun:07:00"  # UTC time
  apply_immediately           = !local.is_production
  skip_final_snapshot         = !local.is_production
  final_snapshot_identifier   = local.is_production ? "${var.name_prefix}-postgres-final-${var.environment}" : null
  
  # Monitoring and performance insights
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  monitoring_interval             = local.is_production ? 60 : 0  # Enhanced monitoring in production
  monitoring_role_arn             = var.monitoring_role_arn
  
  # Security settings
  deletion_protection          = local.is_production
  storage_encrypted            = true
  copy_tags_to_snapshot        = true
  performance_insights_enabled = true
  performance_insights_retention_period = local.is_production ? 731 : 7  # Days: 2 years for prod, 7 days for others
  
  tags = merge({
    Name = "${var.name_prefix}-postgres-${var.environment}"
  }, local.common_tags)
}

# Subnet group for ElastiCache
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.name_prefix}-redis-subnet-group-${var.environment}"
  subnet_ids = var.subnet_ids
  
  tags = merge({
    Name = "${var.name_prefix}-redis-subnet-group-${var.environment}"
  }, local.common_tags)
}

# Parameter group for Redis
resource "aws_elasticache_parameter_group" "redis" {
  name        = "${var.name_prefix}-redis-params-${var.environment}"
  family      = "redis7"
  description = "Parameter group for Redis ${local.redis_engine_version} in ${var.environment} environment"

  # Eviction policy to remove least recently used keys when memory is full
  parameter {
    name  = "maxmemory-policy"
    value = "volatile-lru"
  }

  # Enable keyspace notifications for cache events
  parameter {
    name  = "notify-keyspace-events"
    value = "Kg"
  }

  tags = merge({
    Name = "${var.name_prefix}-redis-params-${var.environment}"
  }, local.common_tags)
}

# Redis ElastiCache cluster
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.name_prefix}-redis-${var.environment}"
  description                = "Redis cluster for ${var.environment} environment"
  node_type                  = local.redis_node_type
  port                       = 6379
  parameter_group_name       = aws_elasticache_parameter_group.redis.name
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.database.id]
  
  # High availability settings
  automatic_failover_enabled = true
  multi_az_enabled           = local.is_production ? true : var.multi_az
  num_cache_clusters         = local.is_production ? 2 : var.redis_nodes
  
  # Security settings
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  # Maintenance and updates
  apply_immediately          = !local.is_production
  auto_minor_version_upgrade = true
  maintenance_window         = "sun:07:00-sun:09:00"  # UTC time
  
  # Backup settings
  snapshot_window            = "05:00-07:00"  # UTC time
  snapshot_retention_limit   = local.is_production ? 7 : 1  # Days
  
  tags = merge({
    Name = "${var.name_prefix}-redis-${var.environment}"
  }, local.common_tags)
}

# Outputs
output "postgres_address" {
  description = "The endpoint address of the PostgreSQL RDS instance"
  value       = aws_db_instance.postgres.address
}

output "postgres_port" {
  description = "The port number of the PostgreSQL RDS instance"
  value       = aws_db_instance.postgres.port
}

output "postgres_database_name" {
  description = "The name of the PostgreSQL database"
  value       = aws_db_instance.postgres.db_name
}

output "db_credentials_secret_arn" {
  description = "The ARN of the Secrets Manager secret containing database credentials"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "redis_primary_endpoint" {
  description = "The primary endpoint address of the Redis ElastiCache cluster"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "redis_reader_endpoint" {
  description = "The reader endpoint address of the Redis ElastiCache cluster for read operations"
  value       = aws_elasticache_replication_group.redis.reader_endpoint_address
}

output "redis_port" {
  description = "The port number of the Redis ElastiCache cluster"
  value       = aws_elasticache_replication_group.redis.port
}

# Variables used by this module (would typically be in variables.tf):
variable "name_prefix" {
  description = "Prefix to be used for resource names"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, production)"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC where resources will be created"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for the database resources"
  type        = list(string)
}

variable "app_security_group_ids" {
  description = "List of security group IDs for the application servers"
  type        = list(string)
}

variable "database_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "interactions"
}

variable "database_username" {
  description = "Username for the PostgreSQL database"
  type        = string
  default     = "interactionapp"
}

variable "multi_az" {
  description = "Whether to enable multi-AZ deployment for non-production environments"
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "Number of days to retain backups for non-production environments"
  type        = number
  default     = 7
}

variable "redis_nodes" {
  description = "Number of Redis nodes for non-production environments"
  type        = number
  default     = 1
}

variable "monitoring_role_arn" {
  description = "ARN of the IAM role for enhanced monitoring"
  type        = string
  default     = null
}

variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}