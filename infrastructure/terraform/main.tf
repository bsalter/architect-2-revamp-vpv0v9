# Main Terraform configuration file for the Interaction Management System
# This file orchestrates the deployment of AWS infrastructure, integrating
# networking, compute, database, security, and monitoring modules to create
# a complete, secure, and scalable environment for the application.

# Define local variables for use throughout the configuration
locals {
  environment_prefix = var.environment == "prod" ? "production" : var.environment
  common_tags = merge(var.tags, {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  })
}

# Networking Module - Creates VPC, subnets, and network security components
module "networking" {
  source = "./modules/networking"
  
  environment              = var.environment
  project_name             = var.project_name
  vpc_cidr                 = var.networking.vpc_cidr
  public_subnets_cidr      = var.networking.public_subnets_cidr
  private_app_subnets_cidr = var.networking.private_app_subnets_cidr
  private_data_subnets_cidr = var.networking.private_data_subnets_cidr
  enable_nat_gateway       = var.networking.enable_nat_gateway
  single_nat_gateway       = var.networking.single_nat_gateway
  enable_vpn_gateway       = var.networking.enable_vpn_gateway
  
  tags = local.common_tags
}

# Security Module - Creates IAM roles, policies, KMS keys, and security groups
module "security" {
  source = "./modules/security"
  
  environment  = var.environment
  project_name = var.project_name
  vpc_id       = module.networking.vpc_id
  
  tags = local.common_tags
}

# Database Module - Creates PostgreSQL RDS instance and Redis ElastiCache
module "database" {
  source = "./modules/database"
  
  environment             = var.environment
  project_name            = var.project_name
  vpc_id                  = module.networking.vpc_id
  private_data_subnet_ids = module.networking.private_data_subnet_ids
  db_security_group_id    = module.networking.database_security_group_id
  cache_security_group_id = module.networking.cache_security_group_id
  kms_key_id              = module.security.kms_key_id
  
  # Database and cache configuration
  database        = var.database
  cache           = var.cache
  enable_multi_az = var.enable_multi_az
  
  tags = local.common_tags
}

# Compute Module - Creates EC2/ECS infrastructure, load balancers, and services
module "compute" {
  source = "./modules/compute"
  
  environment            = var.environment
  project_name           = var.project_name
  vpc_id                 = module.networking.vpc_id
  public_subnet_ids      = module.networking.public_subnet_ids
  private_app_subnet_ids = module.networking.private_app_subnet_ids
  alb_security_group_id  = module.networking.alb_security_group_id
  app_security_group_id  = module.networking.app_security_group_id
  
  # IAM configuration
  instance_profile_name       = module.security.instance_profile_name
  ecs_task_execution_role_arn = module.security.ecs_task_execution_role_arn
  ecs_task_role_arn           = module.security.ecs_task_role_arn
  
  # Service configuration
  domain_name     = var.domain_name
  compute         = var.compute
  frontend_config = var.frontend_config
  backend_config  = var.backend_config
  
  # Database connection information
  db_credentials_secret_arn = module.database.db_credentials_secret_arn
  db_host                   = module.database.db_host
  db_port                   = module.database.db_port
  redis_host                = module.database.redis_host
  redis_port                = module.database.redis_port
  
  # High availability configuration
  enable_multi_az = var.enable_multi_az
  
  tags = local.common_tags
}

# Monitoring Module - Creates CloudWatch dashboards, alarms, and logs
module "monitoring" {
  source = "./modules/monitoring"
  
  environment             = var.environment
  project_name            = var.project_name
  vpc_id                  = module.networking.vpc_id
  alb_arn_suffix          = module.compute.alb_arn_suffix
  ecs_cluster_name        = module.compute.ecs_cluster_name
  db_instance_identifier  = module.database.db_instance_identifier
  cache_cluster_id        = module.database.cache_cluster_id
  frontend_service_name   = module.compute.frontend_service_name
  backend_service_name    = module.compute.backend_service_name
  
  monitoring = var.monitoring
  kms_key_id  = module.security.kms_key_id
  
  tags = local.common_tags
}

# S3 Bucket for static assets storage
resource "aws_s3_bucket" "static_assets" {
  bucket = "${var.project_name}-${var.environment}-static-assets"
  tags   = local.common_tags
}

resource "aws_s3_bucket_acl" "static_assets_acl" {
  bucket = aws_s3_bucket.static_assets.id
  acl    = "private"
}

resource "aws_s3_bucket_versioning" "static_assets_versioning" {
  bucket = aws_s3_bucket.static_assets.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_cors_rule" "static_assets_cors" {
  bucket = aws_s3_bucket.static_assets.id
  
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET"]
    allowed_origins = var.domain_name != null ? ["https://${var.domain_name}"] : ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# CloudFront distribution for static assets delivery
resource "aws_cloudfront_origin_access_identity" "oai" {
  comment = "OAI for ${var.project_name} static assets"
}

resource "aws_cloudfront_distribution" "static_assets_cdn" {
  origin {
    domain_name = aws_s3_bucket.static_assets.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.static_assets.bucket}"
    
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.oai.cloudfront_access_identity_path
    }
  }
  
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  
  aliases = var.domain_name != null ? ["static.${var.domain_name}"] : []
  
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.static_assets.bucket}"
    
    forwarded_values {
      query_string = false
      
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }
  
  price_class = var.environment == "prod" ? "PriceClass_All" : "PriceClass_100"
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    cloudfront_default_certificate = var.domain_name == null
    acm_certificate_arn            = var.domain_name != null ? module.compute.acm_certificate_arn : null
    ssl_support_method             = var.domain_name != null ? "sni-only" : null
    minimum_protocol_version       = var.domain_name != null ? "TLSv1.2_2021" : "TLSv1"
  }
  
  tags = local.common_tags
}

# S3 bucket policy for CloudFront access
resource "aws_s3_bucket_policy" "static_assets_policy" {
  bucket = aws_s3_bucket.static_assets.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "s3:GetObject"
        Effect    = "Allow"
        Resource  = "${aws_s3_bucket.static_assets.arn}/*"
        Principal = {
          AWS = "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity ${aws_cloudfront_origin_access_identity.oai.id}"
        }
      }
    ]
  })
}

# Route 53 records for application endpoints - only created if domain_name is provided
data "aws_route53_zone" "selected" {
  count = var.domain_name != null ? 1 : 0
  name  = var.domain_name
}

resource "aws_route53_record" "www" {
  count   = var.domain_name != null ? 1 : 0
  zone_id = data.aws_route53_zone.selected[0].zone_id
  name    = var.domain_name
  type    = "A"
  
  alias {
    name                   = module.compute.alb_dns_name
    zone_id                = module.compute.alb_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "api" {
  count   = var.domain_name != null ? 1 : 0
  zone_id = data.aws_route53_zone.selected[0].zone_id
  name    = "api.${var.domain_name}"
  type    = "A"
  
  alias {
    name                   = module.compute.alb_dns_name
    zone_id                = module.compute.alb_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "static" {
  count   = var.domain_name != null ? 1 : 0
  zone_id = data.aws_route53_zone.selected[0].zone_id
  name    = "static.${var.domain_name}"
  type    = "A"
  
  alias {
    name                   = aws_cloudfront_distribution.static_assets_cdn.domain_name
    zone_id                = aws_cloudfront_distribution.static_assets_cdn.hosted_zone_id
    evaluate_target_health = false
  }
}

# Output important infrastructure information
output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.networking.vpc_id
}

output "alb_dns_name" {
  description = "The DNS name of the load balancer"
  value       = module.compute.alb_dns_name
}

output "database_endpoint" {
  description = "The endpoint of the database"
  value       = module.database.db_host
  sensitive   = true
}

output "redis_endpoint" {
  description = "The endpoint of the Redis cache"
  value       = module.database.redis_host
  sensitive   = true
}

output "cloudfront_domain_name" {
  description = "The domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.static_assets_cdn.domain_name
}

output "static_assets_bucket" {
  description = "The name of the S3 bucket for static assets"
  value       = aws_s3_bucket.static_assets.bucket
}