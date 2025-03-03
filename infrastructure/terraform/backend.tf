# Backend configuration for Terraform state management
# This configuration stores the Terraform state in an S3 bucket with DynamoDB locking,
# enabling team collaboration and state persistence across deployments.

terraform {
  # Configure the S3 backend for remote state storage
  backend "s3" {
    # S3 bucket that will store the state files
    bucket = "interaction-management-terraform-state"
    
    # Path to the state file within the bucket
    key = "terraform.tfstate"
    
    # AWS region where the S3 bucket and DynamoDB table are located
    region = "us-east-1"
    
    # Enable encryption at rest for the state file
    encrypt = true
    
    # DynamoDB table used for state locking to prevent concurrent modifications
    dynamodb_table = "terraform-state-lock"
    
    # Prefix for different workspace environments (dev, staging, prod)
    # This allows maintaining separate state for each environment using:
    # terraform workspace select dev|staging|prod
    workspace_key_prefix = "env"
  }
}