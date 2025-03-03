# PostgreSQL RDS outputs

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

output "postgres_arn" {
  description = "The ARN of the PostgreSQL RDS instance"
  value       = aws_db_instance.postgres.arn
}

output "db_credentials_secret_arn" {
  description = "The ARN of the Secrets Manager secret containing database credentials"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "db_subnet_group_name" {
  description = "The name of the database subnet group"
  value       = aws_db_subnet_group.postgres.name
}

output "db_security_group_id" {
  description = "The ID of the security group attached to the PostgreSQL RDS instance"
  value       = aws_security_group.database.id
}

# Redis ElastiCache outputs

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

output "redis_security_group_id" {
  description = "The ID of the security group attached to the Redis ElastiCache cluster"
  value       = aws_security_group.redis.id
}

output "redis_arn" {
  description = "The ARN of the Redis ElastiCache cluster"
  value       = aws_elasticache_replication_group.redis.arn
}

# High availability configuration

output "multi_az_enabled" {
  description = "Whether Multi-AZ deployment is enabled for the database resources"
  value       = var.enable_multi_az
}